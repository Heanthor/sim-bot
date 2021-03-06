import json
import logging
import os
import pprint
import time

import unicodedata

from enum import Enum
from queue import Queue
import _thread

from src.api.battlenet import BattleNet
from src.api.simcraft import SimulationCraft
from src.api.warcraftlogs import WarcraftLogs, WarcraftLogsError
from src.connectors.simcraft_connectors.lambda_simcraft_connector import LambdaSimcraftConnector
from src.connectors.simcraft_connectors.local_simcraft_connector import LocalSimcraftConnector
from src.simbot_config import SimBotConfig

logger = logging.getLogger("SimBot")


class SimBotError(Enum):
    SIMCRAFT_ERROR = "SimulationCraft threw an error while running the sim."
    NO_KILLS_LOGGED = "No kills logged for this boss."


# noinspection PyCompatibility
class SimcraftBot:
    def __init__(self, config, bnet=None, warcr=None, simc=None, profiles=None):
        """

        :param config: SimbotConfig
        """
        # create simbot with realm and guild info
        with open(os.path.join(config.params["config_path"], "keys.json"), 'r') as f:
            f = json.loads(f.read())
            warcraft_logs_public = f["warcraftlogs"]["public"]
            battlenet_pub = f["battlenet"]["public"]
            battlenet_sec = f["battlenet"]["secret"]

        if profiles is None:
            with open(os.path.join(config.params["config_path"], "boss_profiles.json"), 'r') as f:
                self._profiles = json.loads(f.read())

        with open(os.path.join(config.params["config_path"], "urls.json"), 'r') as f:
            self._urls = json.loads(f.read())

        self._guild = config.params["guildname"]
        self._realm = config.params["realm"]
        self._region = config.params["region"]
        self._difficulty = config.params["raid_difficulty"]
        self._num_weeks = config.params["weeks_to_examine"]
        self._max_level = config.params["max_level"]
        self._sim_iterations = config.params["simcraft_iterations"]
        self._local_sim = config.params["local_sim"]

        self._blizzard_locale = "en_US"

        self._bnet = bnet or BattleNet(battlenet_pub)
        self._warcr = warcr or WarcraftLogs(warcraft_logs_public)
        self._simc = simc or SimulationCraft(config.params["simc_location"], config.params["simcraft_timeout"],
                                             config.params["config_path"])

        # all players in guild
        self._players_in_guild = []

        # alert thread for sim progress
        self.event_queue = Queue()

        # set by another thread to indicate processing should stop early and result is not wanted
        self._cancelFlag = False

    def cancel_sim(self):
        """
        Causes any running sim job to be cancelled at the earliest opportunity.
        :return:
        """
        self._cancelFlag = True

    def run_all_sims(self):
        """
        Run sims for each DPS player in the guild.
        :return: Guild sim report
        """
        logger.info("Starting sims for guild %s, realm %s, region %s", self._guild, self._realm, self._region)

        names, self._players_in_guild = self._bnet.get_guild_members(self._realm, self._guild, self._blizzard_locale,
                                                                     self._max_level)

        if not self._warcr.has_talent_data():
            self._warcr.set_talent_data(self._bnet.get_all_talents(self._blizzard_locale))

        # playername, sim results
        guild_sims = {}
        # average dps
        guild_percents = []
        # only run sims for 110 dps players

        num_sims = len(names["DPS"])

        self.event_queue.put({
            "start": True,
            "num_sims": num_sims
        })

        if self._local_sim:
            sc = LocalSimcraftConnector()
        else:
            sc = LambdaSimcraftConnector(self._urls)

        for player in names["DPS"]:
            # if self._cancelFlag:
            #     # kill this simbot in the hottest loop
            #     logger.debug("Cancelled job for %s", player["name"])
            #     _thread.exit()
            self.sim_single_character(player["name"], player["realm"], sc)

        all_results = sc.get_completed_sims()

        for item in all_results:
            guild_sims[item["player_name"]] = item

            if item and "error" not in item:
                guild_percents.append(item["average_performance"])
                logger.debug("Finished all sims for character %s in %.2f sec", item["player_name"],
                             item["elapsed_time"])
            else:
                logger.debug("Skipped player %s", item["player_name"])

                self.event_queue.put({
                    "player": item["player_name"],
                    "done": True
                })

        guild_sims["guild_avg"] = sum(guild_percents) / len(guild_percents) if len(guild_percents) > 0 else 0.0

        return guild_sims

    # TODO this can be async as well
    # warcraftlogs can be queried async, but we only spawn async sim processes if data is found
    def sim_single_character(self, player_name, realm, simc_connector):
        """
        Runs full suite of sims on specific character and realm, using the given locale.
        :param player_name:
        :param realm:
        :return:
        """
        if not self._players_in_guild:
            _, self._players_in_guild = self._bnet.get_guild_members(self._realm, self._guild, self._blizzard_locale,
                                                                     self._max_level)

        if player_name not in self._players_in_guild:
            logger.error("Player %s not in guild %s", player_name, self._guild)
            return False

        if not self._warcr.has_talent_data():
            self._warcr.set_talent_data(self._bnet.get_all_talents(self._blizzard_locale))

        try:
            raiding_stats = self._warcr.get_all_parses(player_name, self.realm_slug(realm), self._region,
                                                       "dps", self._difficulty, int(self._num_weeks))
        except WarcraftLogsError as e:
            return {"error": str(e)}

        simc_connector.queue_sim(self.sim_single_suite, player_name, self.realm_slug(realm), self._region,
                                 self._sim_iterations, raiding_stats)

        # self.event_queue.put({
        #     "player": player_name,
        #     "done": True
        # })

        return True

    # unit of work to be parallelized
    async def sim_single_suite(self, player, realm_slug, region, iterations, raiding_stats):
        """
        Produces report on single character's average sims in the form:
         {
         boss name: {"average_dps": _,
                     "num_fights": _,
                      "sim_dps": _,
                      "percent_potential": _
                      },
         "average_performance": _,
         "elapsed_time": _,
         "error": _, (if an error causes the entire result to be useless. Otherwise, errors are per-boss)
         "player_name": _
         }
        :param player:
        :param realm:
        :param raiding_stats:
        :return:
        """
        # each sim is a character, talents, and fight configuration
        #   tag (<character_name><talent string><fight config>)
        sim_cache = {}
        # used to calculate average performance
        scores_lst = []
        scores = {}
        start = time.time()

        scores["bosses"] = []

        for boss_name, stats in raiding_stats.items():
            average_dps = 0.0
            average_percentage = 0.0
            average_ilvl = 0.0

            max_dps = 0.0
            max_dps_talents = []
            max_dps_spec = ""

            if not stats:
                # no kills for this boss on record, but other kills are still present
                scores["bosses"].append({"boss_name": boss_name, "error": SimBotError.NO_KILLS_LOGGED.value})
                continue

            for kill in stats:
                if self._cancelFlag:
                    # kill this simbot in the hottest loop
                    logger.debug("Cancelled job for %s" % player)
                    _thread.exit()

                if kill["dps"] > max_dps:
                    max_dps = kill["dps"]
                    max_dps_spec = kill["spec"].lower()
                    max_dps_talents = kill["talents"]
                average_dps += kill["dps"]
                average_percentage += kill["historical_percent"]
                average_ilvl += kill["ilvl"]

            average_dps /= len(stats)
            average_percentage /= len(stats)
            average_ilvl /= len(stats)

            if max_dps_spec == "beastmastery":
                max_dps_spec = "beast_mastery"

            fight_profile = self._profiles[boss_name]
            tag = hash("%s%s%s" % (player, max_dps_spec, fight_profile))

            # actually run sim
            if tag not in sim_cache:
                sim_results = await self._simc.run_sim(player,
                                                       realm_slug,
                                                       region,
                                                       max_dps_spec,
                                                       ''.join(str(x) for x in max_dps_talents),
                                                       iterations)

                if not sim_results:
                    # simcraft error, results are invalid
                    scores["bosses"].append({"boss_name": boss_name, "error": SimBotError.SIMCRAFT_ERROR.value})
                    sim_cache[tag] = SimBotError.SIMCRAFT_ERROR

                    continue

                sim_cache[tag] = sim_results
            else:
                if isinstance(sim_cache[tag], SimBotError):
                    scores["bosses"].append({"boss_name": boss_name, "error": sim_cache[tag]})

                    continue
                logger.debug("Using cached sim (%s) for player %s spec %s fight config %s", sim_cache[tag], player,
                             max_dps_spec,
                             fight_profile)
                sim_results = sim_cache[tag]

            # result is calculated
            performance_percent = (average_dps / sim_results) * 100

            # add message to be consumed
            self.event_queue.put({
                "player": player,
                "boss": boss_name,
                "done": False
            })

            logger.info("[%s] Average dps (%d fight%s) %d vs sim %d on %s (%d%% of potential)" % (
                player, len(stats), "" if len(stats) == 1 else "s", average_dps, sim_results, boss_name,
                performance_percent))

            scores["bosses"].append({
                "boss_name": boss_name,
                "average_dps": average_dps,
                "num_fights": len(stats),
                "sim_dps": sim_results,
                "percent_potential": performance_percent
            })

            scores_lst.append(performance_percent)

        scores["average_performance"] = sum(scores_lst) / len(scores_lst) if len(scores_lst) != 0 else 0
        scores["elapsed_time"] = time.time() - start
        scores["player_name"] = player

        return scores

    @staticmethod
    def realm_slug(realm):
        """
        Get sanitized realm name for BNET api.
        :param realm:
        :return:
        """
        nfkd_form = unicodedata.normalize('NFKD', realm)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


if __name__ == '__main__':
    # parse cmd line args, start logging
    sbc = SimBotConfig()
    sbc.init_cmd_line()

    sb = SimcraftBot(sbc)

    start = time.time()
    print(json.dumps(sb.run_all_sims()))
    end = time.time() - start

    logger.info("App finished in %.2f seconds (%.2f minutes)", end, end / 60)

import json
import logging
import datetime
import os
import pprint
import time

import unicodedata

import sys

import argparse
from enum import Enum
from queue import Queue
import _thread

from src.api.battlenet import BattleNet
from src.api.simcraft import SimulationCraft
from src.api.warcraftlogs import WarcraftLogs, WarcraftLogsError

logger = logging.getLogger("SimBot")


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


class SimBotError(Enum):
    SIMCRAFT_ERROR = "SimulationCraft threw an error while running the sim."
    NO_KILLS_LOGGED = "No kills logged for this boss."


class SimcraftBot:
    def __init__(self, config, bnet_adapter, warcraftlogs_adapter, simc_adapter, boss_profiles):
        """

        guild: The guild name to run sims for
        realm: The realm
        region: US, EU, KR, TW, CN.
        num_weeks: Number of weeks to look back in time
        max_level: Level of characters to be simmed
        simc_location: Location of simc executable
        """

        self._guild = config.params["guildname"]
        self._realm = config.params["realm"]
        self._region = config.params["region"]
        self._difficulty = config.params["raid_difficulty"]
        self._num_weeks = config.params["weeks_to_examine"]
        self._max_level = config.params["max_level"]
        self._sim_iterations = config.params["simcraft_iterations"]

        self._blizzard_locale = "en_US"

        self._bnet = bnet_adapter
        self._warcr = warcraftlogs_adapter
        self._simc = simc_adapter
        self._profiles = boss_profiles

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

        for player in names["DPS"]:
            if self._cancelFlag:
                # kill this simbot in the hottest loop
                logger.debug("Cancelled job for %s", player["name"])
                _thread.exit()

            results = self.sim_single_character(player["name"], player["realm"])

            guild_sims[player["name"]] = results

            if results and "error" not in results:
                guild_percents.append(results["average_performance"])
                logger.debug("Finished all sims for character %s in %.2f sec", player["name"], results["elapsed_time"])
            else:
                logger.debug("Skipped player %s", player["name"])

                self.event_queue.put({
                    "player": player["name"],
                    "done": True
                })

        guild_sims["guild_avg"] = sum(guild_percents) / len(guild_percents) if len(guild_percents) > 0 else 0.0

        return guild_sims

    def sim_single_character(self, player_name, realm):
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

        to_return = self._sim_single_suite(player_name, realm, raiding_stats)

        self.event_queue.put({
            "player": player_name,
            "done": True
        })

        return to_return

    # TODO this suite will be run in one lambda
    def _sim_single_suite(self, player, realm, raiding_stats):
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
         "error": _ (if an error causes the entire result to be useless. Otherwise, errors are per-boss)
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

            sim_string = "armory=%s,%s,%s spec=%s talents=%s fight_style=%s iterations=%d" % (
                self._region,
                self.realm_slug(realm),
                player, max_dps_spec,
                ''.join(str(x) for x in max_dps_talents),
                fight_profile,
                self._sim_iterations
            )

            # actually run sim
            # TODO this area will be rewritten for async sim results
            if tag not in sim_cache:
                sim_results = self._simc.run_sim(sim_string.split(" "))

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
                logger.debug("Using cached sim for player %s spec %s fight config %s", player, max_dps_spec,
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


class SimBotConfig:
    def __init__(self):
        if sys.version_info < (3, 0):
            sys.exit('Sorry, Python < 2 is not supported')

        self.params = {}

    @staticmethod
    def init_logger(persist, location, write_logs=True):
        if len(logger.handlers):
            # logger has already been initialized by another SimBot
            return

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if write_logs:
            if persist:
                handler = logging.FileHandler(
                    os.path.join(get_script_path(), location, "simbot-%s.log" % time.strftime("%Y%m%d-%H%M%S")))
            else:
                handler = logging.FileHandler(os.path.join(get_script_path(), location, 'simbot.log'), 'w')

            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # stdout logger
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.info("App started at %s", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

    def init_cmd_line(self):
        parser = argparse.ArgumentParser(description='SimBot sim tool.')
        parser.add_argument('guildname', type=str,
                            help='Name of guild to be simmed')
        parser.add_argument('realm', type=str,
                            help='Realm where the guild exists')
        parser.add_argument('simc_location', type=str,
                            help='Absolute path of SimulationCraft CLI executable')
        parser.add_argument('config_path', type=str, default='/',
                            help="Path (relative to __file__) of config directory (including /config")
        parser.add_argument('--simcraft_timeout', type=int, default=5, nargs="?",
                            help='Timeout, in seconds, of each individual simulation.')
        parser.add_argument('--simcraft_iterations', type=int, default=100, nargs="?",
                            help='Simcraft iterations')
        parser.add_argument('--region', type=str, default="US", nargs="?", choices=["US", "EU", "KR", "TW", "CN"],
                            help='Region where guild exists.')
        parser.add_argument('--raid_difficulty', type=str, default="heroic", nargs="?",
                            choices=["lfr", "normal", "heroic", "mythic"],
                            help='Difficulty to filter logs by. ')
        parser.add_argument('--blizzard_locale', type=str, default="en_US", nargs="?",
                            choices=["en_US", "pt_BR", "es_MX"],
                            help='Blizzard language locale,')
        parser.add_argument('--max_level', type=int, default=110, nargs="?",
                            help='Level of characters to sim')
        parser.add_argument('--weeks_to_examine', type=int, default=3, nargs="?",
                            help='Number of weeks of historical logs to average')
        parser.add_argument('--write_logs', type=bool, default=True, nargs='?',
                            help="Save logs to file")
        parser.add_argument('--persist_logs', type=bool, default=False, nargs='?',
                            help="Save logs in separate files, or overwrite single file.")
        parser.add_argument('--log_path', type=str, default="../logs", nargs='?',
                            help="Path (relative to __file__) to save logs to (excluding /<filename>.log)")

        self.params = vars(parser.parse_args())

        self.init_logger(self.params["persist_logs"], self.params["log_path"], self.params["write_logs"])

    def init_args(self, guildname, realm, simc_location, config_path="", simc_timeout=5, simc_iter=100, region="US",
                  raid_difficulty="heroic", blizzard_locale="en_US", max_level=110, weeks_to_examine=3,
                  persist_logs=False, log_path="../logs", write_logs=True):
        """

        :param guildname: The guild name to run sims for (in quotes)
        :param realm: The realm
        :param simc_location: Location of simc executable
        :param config_path: Path (relative to __file__) of config directory (including /config)
        :param simc_timeout: Timeout, in seconds, of each individual simulation.
        :param simc_iter: Simcraft iterations
        :param region: US, EU, KR, TW, CN.
        :param blizzard_locale: en_US
        :param raid_difficulty: normal, heroic, mythic, lfr
        :param weeks_to_examine: Number of weeks to look back in time
        :param max_level: Level of characters to be simmed
        :param persist_logs: Save logs in separate files, or overwrite single file.
        :param log_path: Path (relative to __file__) to save logs to (excluding /<filename>.log)
        :param write_logs: Save logs to file
        """

        self.params["guildname"] = guildname
        self.params["realm"] = realm
        self.params["simc_location"] = simc_location
        self.params["simcraft_timeout"] = simc_timeout
        self.params["simcraft_iterations"] = simc_iter
        self.params["region"] = region
        self.params["raid_difficulty"] = raid_difficulty
        self.params["blizzard_locale"] = blizzard_locale
        self.params["max_level"] = max_level
        self.params["weeks_to_examine"] = weeks_to_examine
        self.params["persist_logs"] = persist_logs
        self.params["log_path"] = log_path
        self.params["config_path"] = config_path
        self.params["write_logs"] = write_logs

        self.init_logger(persist_logs, log_path, write_logs)


if __name__ == '__main__':
    # parse cmd line args, start logging
    sbc = SimBotConfig()
    sbc.init_cmd_line()

    # create simbot with realm and guild info
    with open(os.path.join(sbc.params["config_path"], "keys.json"), 'r') as f:
        f = json.loads(f.read())
        warcraft_logs_public = f["warcraftlogs"]["public"]
        battlenet_pub = f["battlenet"]["public"]
        battlenet_sec = f["battlenet"]["secret"]

    with open(os.path.join(sbc.params["config_path"], "boss_profiles.json"), 'r') as f:
        profiles = json.loads(f.read())

    bnet = BattleNet(battlenet_pub)
    warcr = WarcraftLogs(warcraft_logs_public)
    simc = SimulationCraft(sbc.params["simc_location"], sbc.params["simcraft_timeout"], sbc.params["config_path"])
    sb = SimcraftBot(sbc, bnet, warcr, simc, profiles)

    start = time.time()
    print(json.dumps(sb.run_all_sims()))
    end = time.time() - start

    logger.info("App finished in %.2f seconds (%.2f minutes)", end, end / 60)

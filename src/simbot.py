import json
import logging
import datetime
import pprint
import time

import unicodedata

import sys

import argparse
from enum import Enum

from src.api.battlenet import BattleNet
from src.api.simcraft import SimulationCraft
from src.api.warcraftlogs import WarcraftLogs, WarcraftLogsError

logger = logging.getLogger("SimBot")


class SimBotError(Enum):
    SIMCRAFT_ERROR = 1
    NO_KILLS_LOGGED = 2


class SimcraftBot:
    def __init__(self, guild, realm, region, difficulty, num_weeks, max_level, simc_location, simc_timeout,
                 persist_logs):
        """

        :param guild: The guild name to run sims for
        :param realm: The realm
        :param region: US, EU, KR, TW, CN.
        :param difficulty: lfr, normal, heroic, mythic
        :param num_weeks: Number of weeks to look back in time
        :param max_level: Level of characters to be simmed
        :param simc_location: Location of simc executable
        """
        self._guild = guild
        self._realm = realm
        self._region = region
        self._difficulty = difficulty
        self._num_weeks = num_weeks
        self._max_level = max_level

        self._blizzard_locale = "en_US"

        init_logger(persist_logs)

        with open("../keys.json", 'r') as f:
            f = json.loads(f.read())
            warcraft_logs_public = f["warcraftlogs"]["public"]
            battlenet_pub = f["battlenet"]["public"]
            battlenet_sec = f["battlenet"]["secret"]

        with open("../nighthold_profiles.json", 'r') as f:
            self._profiles = json.loads(f.read())

        self._bnet = BattleNet(battlenet_pub)
        self._warcr = WarcraftLogs(warcraft_logs_public)
        self._simc = SimulationCraft(simc_location, simc_timeout)

        # all players in guild
        self._players_in_guild = []

    def run_all_sims(self):
        """
        Run sims for each DPS player in the guild.
        :return:
        """
        logger.info("Starting sims for guild %s, realm %s, region %s", self._guild, self._realm, self._region)

        names, self._players_in_guild = self._bnet.get_guild_members(self._realm, self._guild, self._blizzard_locale,
                                                                     self._max_level)

        if not self._warcr.has_talent_data():
            self._warcr.set_talent_data(self._bnet.get_all_talents(self._blizzard_locale))

        # playername, sim results
        guild_sims = {}
        # only run sims for 110 dps players
        for player in names["DPS"]:
            results = self.sim_single_character(player["name"], player["realm"])

            guild_sims[player["name"]] = results
            logger.debug("Finished all sims for character %s in %.2f sec", player["name"], results["elapsed_time"])

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

        raiding_stats = self._warcr.get_all_parses(player_name, self.realm_slug(realm), self._region,
                                                   "dps", self._difficulty, self._num_weeks)

        return self._sim_single_suite(player_name, realm, raiding_stats)

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

        if not isinstance(raiding_stats, WarcraftLogsError):
            for boss_name, stats in raiding_stats.items():
                average_dps = 0.0
                average_percentage = 0.0
                average_ilvl = 0.0

                max_dps = 0.0
                max_dps_talents = []
                max_dps_spec = ""

                if not stats:
                    # no kills for this boss on record, but other kills are still present
                    scores[boss_name] = SimBotError.NO_KILLS_LOGGED
                    continue

                for kill in stats:
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

                sim_string = "armory=%s,%s,%s spec=%s talents=%s fight_style=%s" % (self._region,
                                                                                    self.realm_slug(
                                                                                        realm),
                                                                                    player, max_dps_spec,
                                                                                    ''.join(str(x) for x in
                                                                                            max_dps_talents),
                                                                                    fight_profile)

                # actually run sim
                if tag not in sim_cache:
                    sim_results = self._simc.run_sim(sim_string.split(" "))

                    if not sim_results:
                        # simcraft error, results are invalid
                        scores[boss_name] = SimBotError.SIMCRAFT_ERROR
                        sim_cache[tag] = SimBotError.SIMCRAFT_ERROR

                        continue

                    sim_cache[tag] = sim_results
                else:
                    if isinstance(sim_cache[tag], SimBotError):
                        scores[boss_name] = sim_cache[tag]

                        continue
                    logger.debug("Using cached sim for player %s spec %s fight config %s", player, max_dps_spec,
                                 fight_profile)
                    sim_results = sim_cache[tag]

                performance_percent = (average_dps / sim_results) * 100

                logger.info("[%s] Average dps (%d fight%s) %d vs sim %d on %s (%d%% of potential)" % (
                    player, len(stats), "" if len(stats) == 1 else "s", average_dps, sim_results, boss_name,
                    performance_percent))

                scores[boss_name] = {
                    "average_dps": average_dps,
                    "num_fights": len(stats),
                    "sim_dps": sim_results,
                    "percent_potential": performance_percent
                }

                scores_lst.append(performance_percent)
        else:
            # save error for score
            scores["error"] = raiding_stats

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


# def main():
#     logger.warning("TEST")
#
#     with open("keys.json", 'r') as f:
#         f = json.loads(f.read())
#         warcraft_logs_public = f["warcraftlogs"]["public"]
#
#     w = WarcraftLogs(warcraft_logs_public)
#     print w.get_all_parses("Heanthor", "fizzcrank", "US", "dps")

def init_logger(persist):
    logger.setLevel(logging.DEBUG)
    if persist:
        handler = logging.FileHandler("../logs/simbot-%s.log" % time.strftime("%Y%m%d-%H%M%S"))
    else:
        handler = logging.FileHandler('../logs/simbot.log', 'w')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # stdout logger
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info("App started at %s", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))


def init_parser():
    if sys.version_info < (3, 0):
        sys.exit('Sorry, Python < 2 is not supported')

    parser = argparse.ArgumentParser(description='SimBot sim tool.')
    parser.add_argument('guildname', type=str,
                        help='Name of guild to be simmed')
    parser.add_argument('realm', type=str,
                        help='Realm where the guild exists')
    parser.add_argument('simc_location', type=str,
                        help='Absolute path of SimulationCraft CLI executable')
    parser.add_argument('--simcraft_timeout', type=int, default=5, nargs="?",
                        help='Timeout, in seconds, of each individual simulation.')
    parser.add_argument('--region', type=str, default="US", nargs="?", choices=["US", "EU", "KR", "TW", "CN"],
                        help='Region where guild exists.')
    parser.add_argument('--raid_difficulty', type=str, default="heroic", nargs="?",
                        choices=["lfr", "normal", "heroic", "mythic"],
                        help='Difficulty to filter logs by. ')
    parser.add_argument('--blizzard_locale', type=str, default="en_US", nargs="?", choices=["en_US", "pt_BR", "es_MX"],
                        help='Blizzard language locale,')
    parser.add_argument('--max_level', type=int, default=110, nargs="?",
                        help='Level of characters to sim')
    parser.add_argument('--weeks_to_examine', type=int, default=3, nargs="?",
                        help='Number of weeks of historical logs to average')
    parser.add_argument('--persist_logs', type=bool, default=False, nargs='?',
                        help="Save logs in separate files, or overwrite single file.")

    return vars(parser.parse_args())


if __name__ == '__main__':
    args = init_parser()

    sb = SimcraftBot(args["guildname"], args["realm"], args["region"], args["raid_difficulty"],
                     args["weeks_to_examine"], args["max_level"], args["simc_location"],
                     args["simcraft_timeout"], args["persist_logs"])

    start = time.time()
    pprint.pprint(sb.run_all_sims())
    end = time.time() - start

    logger.info("App finished in %.2f seconds (%.2f minutes)", end, end / 60)

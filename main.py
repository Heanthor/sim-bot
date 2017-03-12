import json
import logging

import unicodedata

from api.battlenet import BattleNet
from api.simcraft import SimulationCraft
from api.warcraftlogs import WarcraftLogs

import argparse

logger = logging.getLogger("SimBot")


class SimcraftBot:
    def __init__(self, guild, realm, region, difficulty, num_weeks, max_level, simc_location):
        """
        :param guild: The guild name to run sims for
        :param realm: The realm
        :param region: US, EU, KR, TW, CN.
        """
        self._guild = guild
        self._realm = realm
        self._region = region
        self._difficulty = difficulty
        self._num_weeks = num_weeks
        self._max_level = max_level

        self._blizzard_locale = "en_US"

        with open("keys.json", 'r') as f:
            f = json.loads(f.read())
            warcraft_logs_public = f["warcraftlogs"]["public"]
            battlenet_pub = f["battlenet"]["public"]
            battlenet_sec = f["battlenet"]["secret"]

        with open("nighthold_profiles.json", 'r') as f:
            self._profiles = json.loads(f.read())

        self._bnet = BattleNet(battlenet_pub)
        self._warcr = WarcraftLogs(warcraft_logs_public)
        self._simc = SimulationCraft(simc_location)

        # talent array to be populated by bnet API
        self._talent_info = ""

    def run_sims(self):
        logger.info("Starting sims for guild %s, realm %s, region %s", self._guild, self._realm, self._region)

        names = self._bnet.get_guild_members(self._realm, self._guild, self._blizzard_locale, self._max_level)

        if self._talent_info == "":
            self._talent_info = self._bnet.get_all_talents(self._blizzard_locale)

        # only run sims for 110 dps players
        for player in names["DPS"]:
            raiding_stats = self._warcr.get_all_parses(player["name"], self.realm_slug(player["realm"]), self._region,
                                                       "dps", self._difficulty, self._num_weeks, self._talent_info)

            if raiding_stats:
                for boss_name, stats in raiding_stats.iteritems():
                    average_dps = 0.0
                    average_percentage = 0.0
                    average_ilvl = 0.0

                    max_dps = 0.0
                    max_dps_talents = []
                    max_dps_spec = ""

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

                    sim_string = "armory=%s,%s,%s spec=%s talents=%s fight_style=%s" % (self._region,
                                                                                        self.realm_slug(self._realm),
                                                                                        player["name"], max_dps_spec,
                                                                                        ''.join(str(x) for x in max_dps_talents),
                                                                                        self._profiles[boss_name])

                    sim_results = self._simc.run_sim(sim_string.split(" "))

                    print sim_results

    @staticmethod
    def realm_slug(realm):
        nfkd_form = unicodedata.normalize('NFKD', unicode(realm))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def set_talent_info(self, info):
        self._talent_info = info


def main():
    logger.warning("TEST")

    with open("keys.json", 'r') as f:
        f = json.loads(f.read())
        warcraft_logs_public = f["warcraftlogs"]["public"]

    w = WarcraftLogs(warcraft_logs_public)
    print w.get_all_parses("Heanthor", "fizzcrank", "US", "dps")


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('simbot.log', 'w')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("App started")

    parser = argparse.ArgumentParser(description='SimBot sim tool.')
    parser.add_argument('<guild name>', type=str,
                        help='Name of guild to be simmed')
    parser.add_argument('<realm>', type=str,
                        help='Realm where the guild exists')
    parser.add_argument('<simc location>', type=str,
                        help='Absolute path of SimulationCraft CLI executable')
    parser.add_argument('<region>', type=str, default="US", nargs="?", choices=["US", "EU", "KR", "TW", "CN"],
                        help='Region where guild exists.')
    parser.add_argument('<raid difficulty>', type=str, default="heroic", nargs="?",
                        choices=["lfr", "normal", "heroic", "mythic"],
                        help='Difficulty to filter logs by. ')
    parser.add_argument('<blizzard locale>', type=str, default="en_US", nargs="?", choices=["en_US", "pt_BR", "es_MX"],
                        help='Blizzard language locale,')
    parser.add_argument('<max level>', type=int, default=110, nargs="?",
                        help='Level of characters to sim')
    parser.add_argument('<weeks to examine>', type=int, default=3, nargs="?",
                        help='Number of weeks of historical logs to average')

    args = vars(parser.parse_args())

    sb = SimcraftBot(args["<guild name>"], args["<realm>"], args["<region>"], args["<raid difficulty>"],
                     args["<weeks to examine>"], args["<max level>"], args["<simc location>"])

    sb.run_sims()

    logger.info("App finished")

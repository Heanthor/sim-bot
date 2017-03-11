import json
import logging

import unicodedata

from api.battlenet import BattleNet
from api.warcraftlogs import WarcraftLogs

import argparse


class SimcraftBot:
    def __init__(self, guild, realm, region, max_level=110):
        """

        :param guild: The guild name to run sims for
        :param realm: The realm
        :param region: US, EU, KR, TW, CN.
        """
        self._guild = guild
        self._realm = realm
        self._region = region
        self._max_level = max_level

        self._blizzard_locale = "en_US"

        with open("keys.json", 'r') as f:
            f = json.loads(f.read())
            warcraft_logs_public = f["warcraftlogs"]["public"]
            battlenet_pub = f["battlenet"]["public"]
            battlenet_sec = f["battlenet"]["secret"]

        self._bnet = BattleNet(battlenet_pub)
        self._warcr = WarcraftLogs(warcraft_logs_public)

    def run_sims(self):
        names = self._bnet.get_guild_members(self._realm, self._guild, self._blizzard_locale, self._max_level)

        # only run sims for 110 dps players
        for player in names["DPS"]:
            pass

    @staticmethod
    def realm_slug(realm):
        nfkd_form = unicodedata.normalize('NFKD', unicode(realm))
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def main():
    logging.basicConfig(filename="simbot.log", level=logging.DEBUG)
    logging.info("App started")

    with open("keys.json", 'r') as f:
        f = json.loads(f.read())
        warcraft_logs_public = f["warcraftlogs"]["public"]

    w = WarcraftLogs(warcraft_logs_public)
    print w.get_all_parses("Heanthor", "fizzcrank", "US", "dps")

    logging.info("App finished")


def battlenet_test():
    with open("keys.json", 'r') as f:
        f = json.loads(f.read())
        battlenet_pub = f["battlenet"]["public"]
        battlenet_sec = f["battlenet"]["secret"]

    b = BattleNet(battlenet_pub)
    print b.get_guild_members("Fizzcrank", "Clutch", "en_US")
    # client = BackendApplicationClient(client_id=battlenet_pub)
    # oauth = OAuth2Session(client=client)
    # token = oauth.fetch_token(token_url='https://us.battle.net/oauth/token', client_id=battlenet_pub,
    #                           client_secret=battlenet_sec)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SimBot sim tool.')
    parser.add_argument('<guild name>', type=str,
                        help='Name of guild to be simmed')
    parser.add_argument('<realm>', type=str,
                        help='Realm where the guild exists')
    parser.add_argument('<region>', type=str, default="US", nargs="?",
                        help='Region where guild exists (US, EU, KR, TW, CN.)')
    parser.add_argument('<blizzard locale>', type=str, default="en_US", nargs="?",
                        help='Blizzard language locale (en_US, pt_BR, es_MX')
    parser.add_argument('<max level>', type=int, default=110, nargs="?",
                        help='Level of characters to sim')

    args = vars(parser.parse_args())

    sb = SimcraftBot(args["<guild name>"], args["<realm>"], args["<region>"], args["<max level>"])
    sb.run_sims()

import requests
import logging
from collections import defaultdict

API_URL = "https://us.api.battle.net/"
logger = logging.getLogger()


class BattleNet:
    def __init__(self, api_key):
        self._api_key = api_key

    def get_guild_members(self, realm, guild_name, locale, level):
        """
        Gets list of max level guild members and their roles, in the form:
        { DPS: [],
          HEALING: [],
          TANK: []
        }
        :param realm: Realm guild is located on
        :param guild_name: The guild to query for
        :param locale: en_US or other
        :param level: Return only players at this level
        :return: Dict of guild members and their role
        """
        r = requests.get(API_URL + "wow/guild/%s/%s" % (realm, guild_name),
                         params={"fields": "members", "locale": locale, "apikey": self._api_key})

        raw = r.json()
        names = defaultdict(list)

        try:
            members_raw = raw["members"]
        except KeyError:
            logger.error("Unable to retrieve bnet guild list for guild %s, realm %s, locale %s", guild_name, realm,
                         locale)
            return {}

        for character in members_raw:
            character = character["character"]
            if character["level"] == level:
                names[character["spec"]["role"]].append({
                    "name": character["name"],
                    "realm": character["realm"],
                })

        return names

import requests

API_URL = "https://us.api.battle.net/"


class BattleNet:
    def __init__(self, api_key):
        self._api_key = api_key

    def get_guild_members(self, realm, guild_name, locale):
        """
        Returns JSON array of guild members, using Blizzard battle.net API.
        Format:

            {
            "lastModified": 0,
            "name": "",
            "realm": "",
            "battlegroup": "",
            "level": 25,
            "side": 1 (Horde),
            "achievementPoints": ,
            "members": [{
                "character": {
                    "name": "",
                    "realm": "",
                    "battlegroup": "",
                    "class": (class code int),
                    "race": (race code int),
                    "gender": (0 M, 1 F),
                    "level": 110,
                    "achievementPoints": 0,
                    "thumbnail": "",
                    "spec": {
                        "name": "",
                        "role": "DPS",
                        "backgroundImage": "",
                        "icon": "",
                        "description": "",
                        "order": 0
                    },
                    "guild": "",
                    "guildRealm": "",
                    "lastModified": 0
                },
                "rank": 0
            },
        :param realm: Realm guild is located on
        :param guild_name: The guild to query for
        :param locale: en_US or other
        :return: JSON API response
        """
        r = requests.get(API_URL + "wow/guild/%s/%s" % (realm, guild_name),
                         params={"fields": "members", "locale": locale, "apikey": self._api_key})

        return r.json()

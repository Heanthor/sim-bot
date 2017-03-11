import requests

API_URL = "https://www.warcraftlogs.com:443/v1/"


class WarcraftLogs:
    def __init__(self, api_key):
        self._api_key = api_key

    def get_reports(self, guild_name, server, region):
        r = requests.get(API_URL + "reports/guild/%s/%s/%s" % (guild_name, server, region),
                         params={"api_key": self._api_key})
        return r.json()

    def get_all_parses(self, character_name, server, region, metric):
        r = requests.get(API_URL + "parses/character/%s/%s/%s" % (character_name, server, region),
                         params={"metric": metric, "api_key": self._api_key})

        try:
            return r.json()
        except ValueError:
            print r.text

            return []

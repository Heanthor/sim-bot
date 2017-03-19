import requests
import logging
from collections import defaultdict

import time

API_URL = "https://us.api.battle.net/"
logger = logging.getLogger("SimBot")


class BattleNet:
    # API rate limits
    BNET_MAX_CALLS_SEC = 100
    BNET_MAX_CALLS_HR = 36000

    def __init__(self, api_key):
        self._api_key = api_key

        # running totals of API calls quota
        self._calls_sec = 0
        self._calls_hr = 0

        self._sec_ticker = time.time()
        self._hr_ticker = time.time()

    def get_guild_members(self, realm, guild_name, locale, level):
        """
        Gets list of max level guild members and their roles, in the form:
        { DPS: [{
                name: "",
                realm: "",
                }
          HEALING: [..],
          TANK: [..]
        }
        :param realm: Realm guild is located on
        :param guild_name: The guild to query for
        :param locale: en_US or other
        :param level: Return only players at this level
        :return: Dict of guild members and their role, and a simple list of all names
        """
        r = self.bnet_request(requests.get, API_URL + "wow/guild/%s/%s" % (realm, guild_name),
                              params={"fields": "members", "locale": locale, "apikey": self._api_key})

        raw = r.json()
        names = defaultdict(list)
        basic_names = []

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
                basic_names.append(character["name"])

        return names, basic_names

    def get_all_talents(self, locale):
        r = self.bnet_request(requests.get, API_URL + "wow/data/talents", params={"locale": locale,
                                                                                  "apikey": self._api_key})

        return r.json()

    def bnet_request(self, req_func, *args, **kwargs):
        if self._calls_sec > self.BNET_MAX_CALLS_SEC:
            logger.error("API call/sec rate %d exceeded max %d", self._calls_sec, self.BNET_MAX_CALLS_SEC)
        elif self._calls_hr > self.BNET_MAX_CALLS_HR:
            logger.error("API call/hr rate %d exceeded max %d", self._calls_hr, self.BNET_MAX_CALLS_HR)

        r = req_func(*args, **kwargs)

        logger.debug("Bnet request sent (%s). In last hour: %d", r.url, self._calls_hr)
        self._calls_sec += 1
        self._calls_hr += 1

        # reset quotas if time is up
        curr_time = time.time()

        if curr_time - self._sec_ticker >= 1:
            self._calls_sec = 0
            self._sec_ticker = curr_time

        if curr_time - self._hr_ticker >= 3600:
            self._calls_hr = 0
            self._hr_ticker = curr_time

        return r

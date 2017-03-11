import logging
from time import time
import requests
from datetime import timedelta

API_URL = "https://www.warcraftlogs.com:443/v1/"
logger = logging.getLogger("SimBot")


class WarcraftLogs:
    DIFFICULTY_DICT = {
        "lfr": 2,
        "normal": 3,
        "heroic": 4,
        "mythic": 5,
    }

    def __init__(self, api_key):
        self._api_key = api_key

    def get_reports(self, guild_name, server, region):
        r = requests.get(API_URL + "reports/guild/%s/%s/%s" % (guild_name, server, region),
                         params={"api_key": self._api_key})
        try:
            return r.json()
        except ValueError:
            print r.text

            return []

    def get_all_parses(self, character_name, server, region, metric, difficulty, num_weeks):
        r = requests.get(API_URL + "parses/character/%s/%s/%s" % (character_name, server, region),
                         params={"metric": metric, "api_key": self._api_key})

        raw = r.json()

        if not raw:
            logger.debug("Empty warcraftlogs response for character %s, server %s, region %s, difficulty %s",
                         character_name, server, region, difficulty)
            return []
        elif r.status_code != 200:
            logger.debug(
                "Unable to find parses for character %s, server %s, region %s, difficulty %s",
                character_name, server, region, difficulty)
            return []

        kills_per_boss = {}
        for boss in raw:
            if boss["difficulty"] != self.DIFFICULTY_DICT[difficulty]:
                # skip logs not at our difficulty
                continue

            # "Skorpyron" for example
            boss_name = boss["name"]
            kills_in_time = []

            for spec in boss["specs"]:
                spec_str = spec["spec"]
                if spec_str == "Melee" or spec_str == "Ranged":
                    # Ignore duplicated array for "all specs"
                    continue

                # "Arms" for example

                for kill in spec["data"]:
                    # filter everything older than x weeks
                    # curr_time - lookback time < log_time
                    lookback_time = timedelta(days=num_weeks * 7).total_seconds()
                    log_time = kill["start_time"] / 1000
                    curr_time = time()

                    if (curr_time - lookback_time) > log_time:
                        # log is too long ago
                        continue
                    else:
                        logger.debug("Found good log of player %s on boss %s", character_name, boss_name)

                        ilvl = kill["ilvl"]
                        dps = kill["persecondamount"]
                        historical_percent = kill["historical_percent"]
                        talents = kill["talents"]
                        # gear will be pulled from blizzard API

                        kills_in_time.append({
                            "ilvl": ilvl,
                            "dps": dps,
                            "historical_percent": historical_percent,
                            "spec": spec_str,
                            "talents": talents,
                        })

            kills_per_boss[boss_name] = kills_in_time

        return kills_per_boss
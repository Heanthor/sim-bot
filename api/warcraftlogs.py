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

    def get_all_parses(self, character_name, server, region, metric, difficulty, num_weeks, talent_data):
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

                # "Warrior" for example
                class_str = spec["class"]

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
                        logger.debug("Found usable log of player %s on boss %s", character_name, boss_name)

                        ilvl = kill["ilvl"]
                        dps = kill["persecondamount"]
                        historical_percent = kill["historical_percent"]
                        talents = self.convert_talents(class_str, spec_str, kill["talents"], talent_data)
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

    @staticmethod
    def convert_talents(class_str, spec_str, warcraftlogs_talents, blizzard_talents):
        """
        Convert from warcraftlogs talent format to blizzard talent format
        :param class_str:
        :param spec_str:
        :param warcraftlogs_talents:
        :param blizzard_talents:
        :return:
        """

        temp = []

        counter = 0
        for talent in warcraftlogs_talents:
            for entry in blizzard_talents.itervalues():
                if entry["class"].replace("-", '').lower() == class_str.lower():
                    talent_object = entry["talents"]
                    tier = talent_object[counter]

                    done_tier = False
                    for talent_entry in tier:
                        for talent_for_spec in talent_entry:
                            if "spec" in talent_for_spec:
                                if talent_for_spec["spec"]["name"].lower().replace(" ", "") == spec_str.lower() and \
                                                talent_for_spec["spell"]["id"] == talent["id"]:
                                    temp.append(talent_for_spec["column"])
                                    done_tier = True
                                    break
                            else:
                                # talent is the same for all 3 specs
                                temp.append(talent_for_spec["column"])
                                done_tier = True
                                break
                        if done_tier:
                            break

                    counter += 1
        return temp

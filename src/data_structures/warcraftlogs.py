import logging

from datetime import timedelta
from time import time

logger = logging.getLogger("SimBot")


class ParseResponse:
    # WarcraftLogs difficulty codes
    LFR = 2
    NORMAL = 3
    HEROIC = 4
    MYTHIC = 5

    def __init__(self, json_response):
        self.r = json_response

        self._difficulty_dict = {
            "lfr": 2,
            "normal": 3,
            "heroic": 4,
            "mythic": 5,
        }

        self._kills = {}

    def filter_kills(self, num_days, difficulty_value=NORMAL):
        kills = {}

        if num_days <= 0:
            logger.error("Number of days cannot be <= 0.")
            return False

        # convert string to int difficulty value
        difficulty = difficulty_value
        if isinstance(difficulty_value, str):
            if difficulty_value.lower() not in self._difficulty_dict:
                logger.error("Unable to coerce difficulty value %s", difficulty_value)

                return False
            else:
                difficulty = self._difficulty_dict[difficulty_value.lower()]

        kills_per_boss = {}
        for boss in self.r:
            if boss["difficulty"] != difficulty:
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
                    lookback_time = timedelta(days=num_days).total_seconds()
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
                        talents = WarcraftLogs.convert_talents(class_str, spec_str, kill["talents"], talent_data)
                        # gear will be pulled from blizzard API

                        kills_in_time.append({
                            "ilvl": ilvl,
                            "dps": dps,
                            "historical_percent": historical_percent,
                            "spec": spec_str,
                            "talents": talents,
                        })

            kills_per_boss[boss_name] = kills_in_time

        return True

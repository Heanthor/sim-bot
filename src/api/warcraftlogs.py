import logging
from time import time
import datetime
import requests
from datetime import timedelta

API_URL = "https://www.warcraftlogs.com:443/v1/"
logger = logging.getLogger("SimBot")


class WarcraftLogsError(Exception):
    EMPTY_RESPONSE = 1
    NO_RECENT_KILLS = 2
    SERVER_ERROR = 3
    OTHER_ERROR = 4


class WarcraftLogs:
    DIFFICULTY_DICT = {
        "lfr": 2,
        "normal": 3,
        "heroic": 4,
        "mythic": 5,
    }

    BNET_CLASS_MAPPING = {
        "warrior": "1",
        "monk": "10",
        "druid": "11",
        "demonhunter": "12",
        "paladin": "2",
        "hunter": "3",
        "rogue": "4",
        "priest": "5",
        "deathknight": "6",
        "shaman": "7",
        "mage": "8",
        "warlock": "9"
    }

    def __init__(self, api_key):
        self._api_key = api_key

        self._talent_data = {}

    def get_reports(self, guild_name, server, region):
        r = self.warcraftlogs_request(requests.get, API_URL + "reports/guild/%s/%s/%s" % (guild_name, server, region),
                                      params={"api_key": self._api_key})
        try:
            return r.json()
        except ValueError:
            print(r.text)

            return []

    def get_all_parses(self, character_name, server, region, metric, difficulty, num_weeks):
        """
        Get all parse information on a specific player. This includes all boss kills on record, on all difficulties.
        :param character_name:
        :param server:
        :param region:
        :param metric:
        :param difficulty:
        :param num_weeks:
        :return:
        """

        if num_weeks <= 0:
            logger.error("Number of weeks cannot be <= 0.")
            return False

        if not character_name or not server or not region or not metric or not difficulty:
            message = "Some parameters missing: name '%s', server '%s', region '%s', metric '%s', difficulty '%s'" % (
                character_name, server, region, metric, difficulty
            )

            logger.error(message)
            raise ValueError(message)

        # convert string to int difficulty value
        difficulty_normalized = difficulty
        if isinstance(difficulty, str):
            if difficulty.lower() not in self.DIFFICULTY_DICT:
                logger.error("Unable to coerce difficulty value %s", difficulty)

                return False
            else:
                difficulty_normalized = self.DIFFICULTY_DICT[difficulty.lower()]

        r = self.warcraftlogs_request(requests.get,
                                      API_URL + "parses/character/%s/%s/%s" % (character_name, server, region),
                                      params={"metric": metric, "api_key": self._api_key})

        raw = r.json()

        if not raw:
            logger.error("Empty warcraftlogs response for character %s, server %s, region %s, difficulty %s",
                         character_name, server, region, difficulty)
            raise WarcraftLogsError("No logs on record.")
        elif r.status_code != 200:
            logger.error(
                "Unable to find parses for character %s, server %s, region %s, difficulty %s",
                character_name, server, region, difficulty)
            raise WarcraftLogsError("WarcraftLogs server error %d" % r.status_code)

        process_result = self.process_parses(character_name, difficulty_normalized, num_weeks, raw)

        for v in process_result.values():
            if v:
                # at least one boss entry has data
                return process_result

        # all boss entries are empty, player is in guild but has not raided
        logger.info("Player %s has no boss kills in past %d weeks.", character_name, num_weeks)

        raise WarcraftLogsError("No kills in the given time window.")

    def process_parses(self, character_name, difficulty_normalized, num_weeks, response_json):
        """
        No error checking or logging, helper method to process parses from WarcraftLogs.
        Will filter out generic "Ranged" or "Melee" reports (actual reports under their class/spec are duplicated).
        Filters out reports older than x weeks. Filters out reports not at the specified difficulty.
        :param character_name:
        :param difficulty_normalized:
        :param num_weeks:
        :param response_json:
        :return:
        """
        kills_per_boss = {}

        for boss in response_json:
            if boss["difficulty"] != difficulty_normalized:
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
                        logger.debug("Found usable log of player '%s' on boss '%s' from '%s'", character_name,
                                     boss_name,
                                     datetime.datetime.fromtimestamp(log_time).strftime('%Y-%m-%d %H:%M:%S'))

                        ilvl = kill["ilvl"]
                        dps = kill["persecondamount"]
                        historical_percent = kill["historical_percent"]
                        talents = self.convert_talents(class_str, spec_str, kill["talents"])
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
    def warcraftlogs_request(req_func, *args, **kwargs):
        start = time()
        r = req_func(*args, **kwargs)
        dur = time() - start
        logger.debug("Warcraftlogs request complete (%d ms) - (%s)", dur, r.url)

        return r

    def convert_talents(self, class_str, spec_str, warcraftlogs_talents):
        """
        Convert from warcraftlogs talent format to column number format (e.g. 0011221)
        :param class_str:
        :param spec_str:
        :param warcraftlogs_talents:
        :return:
        """

        temp = []

        counter = 0

        # Simc talents are 1-indexed instead of 0, for the time being (pending fix)
        simc_offset = 1

        if not self.has_talent_data():
            logger.critical("Blizzard talents not set for WarcraftLogs!")
            raise RuntimeError("Blizzard talents not set for WarcraftLogs!")

        for talent in warcraftlogs_talents:
            entry = self._talent_data[WarcraftLogs.BNET_CLASS_MAPPING[class_str.lower()]]
            tier = entry["talents"][counter]

            done_tier = False
            for talent_entry in tier:
                for talent_for_spec in talent_entry:
                    # One talent for each 3 (or 2, or 4) specs
                    if "spec" in talent_for_spec:
                        if talent_for_spec["spec"]["name"].lower().replace(" ", "") == spec_str.lower() and \
                                        talent_for_spec["spell"]["id"] == talent["id"]:
                            temp.append(talent_for_spec["column"] + simc_offset)
                            done_tier = True
                            break
                    else:
                        # talent is the same for all 3 specs
                        if talent_for_spec["spell"]["id"] == talent["id"]:
                            temp.append(talent_for_spec["column"] + simc_offset)
                            done_tier = True
                            break
                if done_tier:
                    break

            counter += 1
        return temp

    def has_talent_data(self):
        return self._talent_data != {}

    def set_talent_data(self, talent_data):
        """
        Set talent data from Bnet API.
        :param talent_data:
        :return:

        """
        self._talent_data = talent_data

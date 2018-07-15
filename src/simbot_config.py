import argparse
import logging
import os

import sys

import time

import datetime

logger = logging.getLogger("SimBot")


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


class SimBotConfig:
    def __init__(self):
        if sys.version_info < (3, 0):
            sys.exit('Sorry, Python < 2 is not supported')

        self.params = {}

    @staticmethod
    def init_logger(persist, location, write_logs=True):
        if len(logger.handlers):
            # logger has already been initialized by another SimBot
            return

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if write_logs:
            if persist:
                handler = logging.FileHandler(
                    os.path.join(get_script_path(), location, "simbot-%s.log" % time.strftime("%Y%m%d-%H%M%S")))
            else:
                handler = logging.FileHandler(os.path.join(get_script_path(), location, 'simbot.log'), 'w')

            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # stdout logger
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.info("App started at %s", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

    def init_cmd_line(self):
        parser = argparse.ArgumentParser(description='SimBot sim tool.')
        parser.add_argument('guildname', type=str,
                            help='Name of guild to be simmed')
        parser.add_argument('realm', type=str,
                            help='Realm where the guild exists')
        parser.add_argument('simc_location', type=str,
                            help='Absolute path of SimulationCraft CLI executable')
        parser.add_argument('local_sim', type=bool, default=True,
                            help='True to run sims locally, false to run sims on Lambda')
        parser.add_argument('config_path', type=str, default='/',
                            help="Path (relative to __file__) of config directory (including /config")
        parser.add_argument('--simcraft_timeout', type=int, default=5, nargs="?",
                            help='Timeout, in seconds, of each individual simulation.')
        parser.add_argument('--simcraft_iterations', type=int, default=100, nargs="?",
                            help='Simcraft iterations')
        parser.add_argument('--region', type=str, default="US", nargs="?", choices=["US", "EU", "KR", "TW", "CN"],
                            help='Region where guild exists.')
        parser.add_argument('--raid_difficulty', type=str, default="heroic", nargs="?",
                            choices=["lfr", "normal", "heroic", "mythic"],
                            help='Difficulty to filter logs by. ')
        parser.add_argument('--blizzard_locale', type=str, default="en_US", nargs="?",
                            choices=["en_US", "pt_BR", "es_MX"],
                            help='Blizzard language locale,')
        parser.add_argument('--max_level', type=int, default=110, nargs="?",
                            help='Level of characters to sim')
        parser.add_argument('--weeks_to_examine', type=int, default=3, nargs="?",
                            help='Number of weeks of historical logs to average')
        parser.add_argument('--write_logs', type=bool, default=True, nargs='?',
                            help="Save logs to file")
        parser.add_argument('--persist_logs', type=bool, default=False, nargs='?',
                            help="Save logs in separate files, or overwrite single file.")
        parser.add_argument('--log_path', type=str, default="../logs", nargs='?',
                            help="Path (relative to __file__) to save logs to (excluding /<filename>.log)")

        self.params = vars(parser.parse_args())

        self.init_logger(self.params["persist_logs"], self.params["log_path"], self.params["write_logs"])

    def init_args(self, guildname, realm, simc_location, local_sim=True, config_path="", simc_timeout=5, simc_iter=100,
                  region="US",
                  raid_difficulty="heroic", blizzard_locale="en_US", max_level=110, weeks_to_examine=3,
                  persist_logs=False, log_path="../logs", write_logs=True):
        """

        :param guildname: The guild name to run sims for (in quotes)
        :param realm: The realm
        :param simc_location: Location of simc executable
        :param local_sim: True to run sims locally, false to run on Lambda
        :param config_path: Path (relative to __file__) of config directory (including /config)
        :param simc_timeout: Timeout, in seconds, of each individual simulation.
        :param simc_iter: Simcraft iterations
        :param region: US, EU, KR, TW, CN.
        :param blizzard_locale: en_US
        :param raid_difficulty: normal, heroic, mythic, lfr
        :param weeks_to_examine: Number of weeks to look back in time
        :param max_level: Level of characters to be simmed
        :param persist_logs: Save logs in separate files, or overwrite single file.
        :param log_path: Path (relative to __file__) to save logs to (excluding /<filename>.log)
        :param write_logs: Save logs to file
        """

        self.params["guildname"] = guildname
        self.params["realm"] = realm
        self.params["simc_location"] = simc_location
        self.params["local_sim"] = local_sim
        self.params["simcraft_timeout"] = simc_timeout
        self.params["simcraft_iterations"] = simc_iter
        self.params["region"] = region
        self.params["raid_difficulty"] = raid_difficulty
        self.params["blizzard_locale"] = blizzard_locale
        self.params["max_level"] = max_level
        self.params["weeks_to_examine"] = weeks_to_examine
        self.params["persist_logs"] = persist_logs
        self.params["log_path"] = log_path
        self.params["config_path"] = config_path
        self.params["write_logs"] = write_logs

        self.init_logger(persist_logs, log_path, write_logs)
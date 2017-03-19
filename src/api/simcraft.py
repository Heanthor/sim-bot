import json
import logging
import os

import subprocess

import sys

logger = logging.getLogger("SimBot")


class SimulationCraft:
    def __init__(self, simc_path):
        if not os.path.isfile(simc_path):
            logger.error("Unable to find simcraft executable at location %s", simc_path)
            raise RuntimeError("Unable to find simcraft executable at location " + simc_path)
        else:
            logger.info("Found simcraft executable at %s", simc_path)
            self._simc_path = simc_path

        if not simc_path.endswith("simc.exe") and not simc_path.endswith("simc"):
            logging.error("Simc path incomplete (must end with simc executable")
            raise RuntimeError("Simc path incomplete (must end with simc executable")

        with open("../nighthold_profiles.json", 'r') as f:
            self._nighthold_profile = json.loads(f.read())

    def run_sim(self, param_list):
        logger.debug("Simming with string %s", " ".join(param_list))

        output = subprocess.check_output([self._simc_path] + param_list).replace('\r', '').replace('\n', '')
        return int(self.find_dps(output))

    @staticmethod
    def find_dps(string):
        # regex does not work here, do it the old fashioned way
        marker = "DPS Ranking:"
        tag = string.index(marker) + len(marker) + 1
        new_str = string[tag:tag + 20]
        x = new_str[:new_str.index(" ")]

        if not x:
            logging.error("Unable to find DPS in string")
            x = 1

        return x

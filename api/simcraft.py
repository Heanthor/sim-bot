import json
import logging
import os

import subprocess

logger = logging.getLogger("SimBot")

class SimulationCraft:
    def __init__(self, simc_path):
        if not os.path.isfile(simc_path):
            logger.error("Unable to find simcraft executable at location %s", simc_path)
            self._simc_path = ""
        else:
            logger.info("Found simcraft executable at %s", simc_path)
            self._simc_path = simc_path

        with open("nighthold_profiles.json", 'r') as f:
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
        return new_str[:new_str.index(" ")]

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

    def run_sim(self, *args):
        return subprocess.check_output(self._simc_path, *args)


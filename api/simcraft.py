import logging

import subprocess

logger = logging.getLogger("SimBot")


class SimulationCraft:
    def __init__(self, simc_path):
        self._simc_path = simc_path

    def run_sim(self, *args):
        subprocess.check_output(self._simc_path, *args)

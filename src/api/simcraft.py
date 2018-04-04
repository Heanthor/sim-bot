import json
import logging
import multiprocessing
import os

import subprocess

from multiprocessing.pool import ThreadPool

logger = logging.getLogger("SimBot")


class SimulationCraft:
    def __init__(self, simc_path, simc_timeout, config_path):
        if not os.path.isfile(simc_path):
            logger.error("Unable to find simcraft executable at location %s", simc_path)
            raise RuntimeError("Unable to find simcraft executable at location " + simc_path)
        else:
            logger.info("Found simcraft executable at %s", simc_path)
            self._simc_path = simc_path

        if not simc_path.endswith("simc.exe") and not simc_path.endswith("simc"):
            logging.error("Simc path incomplete (must end with simc executable")
            raise RuntimeError("Simc path incomplete (must end with simc executable")

        with open(os.path.join(config_path, "boss_profiles.json"), 'r') as f:
            self._nighthold_profile = json.loads(f.read())

        self._simc_timeout = simc_timeout

    def run_sim(self, param_list):
        """
        Runs a sim (through a subprocess) with the given params
        :param param_list: The string to run with, e.g. armory=US,Fizzcrank,xxx spec=elemental talents=0001220
                                                        fight_style=HecticAddCleave
        :return: The resulting simmed DPS, or False if sim timed out
        """
        sim_string = " ".join(param_list)
        logger.debug("Simming with string %s", sim_string)

        pool = ThreadPool(processes=1)
        async_output = pool.apply_async(self.simcraft_proc_worker, (param_list,))

        try:
            output = async_output.get(timeout=self._simc_timeout)
        except multiprocessing.context.TimeoutError:
            # HecticAddCleave can take a long time on some specs -- make the timeout generous to avoid skipping any
            logger.error("Sim timed out with string %s, skipping." % sim_string)

            # windows kill process
            if os.name == "nt":
                subprocess.check_call('taskkill /im simc.exe /t /f')
            else:
                # TODO linux/mac
                pass

            return False
        return int(self.find_dps(output))

    def simcraft_proc_worker(self, param_list):
        return str(subprocess.check_output([self._simc_path] + param_list).replace(b'\r', b'').replace(b'\n', b''))

    @staticmethod
    def find_dps(string):
        # regex does not work here, do it the old fashioned way
        marker = "DPS Ranking:"
        tag = string.index(marker) + len(marker) - 1
        col_loc = string[tag:].index(":")
        if string[tag + col_loc + 1] == " ":
            # 6 digit number
            new_str = string[tag + 2:tag + 20]
            x = new_str[:new_str.index(" ")]
        else:
            # 7 digit number
            new_str = string[tag + 1:tag + 20]
            x = new_str[:new_str.index(" ")]

        if not x:
            logger.error("Unable to find DPS in string")
            return False

        return x

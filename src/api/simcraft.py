import asyncio
import json
import logging
import os

logger = logging.getLogger("SimBot")


class SimulationcraftProcessError(Exception):
    pass


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
            self.boss_profiles = json.loads(f.read())

        self._simc_timeout = simc_timeout

    async def run_sim(self, character_name, realm_slug, region, spec, talent_string, iterations, simc_stderr=False):
        """
        Runs an async sim with the given params
        :param iterations: Simcraft iterations
        :param talent_string: Simcraft talent string, 7 digits 1-3
        :param spec: Spec string
        :param region: Realm region
        :param realm_slug: Realm slug
        :param character_name: Character name
        :param simc_stderr: Pipe stderr back to python? Seems to not work on Windows
        :return: Coroutine containing the resulting simmed DPS, or False if sim timed out
        """

        sim_string = "armory=%s,%s,%s spec=%s talents=%s iterations=%d" % (
            region, realm_slug, character_name, spec, talent_string, iterations)
        logger.debug("Simming with string %s", sim_string)

        shell_cmd = "%s %s" % (self._simc_path, sim_string)

        if simc_stderr:
            stderr_pipe = asyncio.subprocess.PIPE
        else:
            stderr_pipe = None

        proc_handle = await asyncio.create_subprocess_shell(shell_cmd, stdout=asyncio.subprocess.PIPE,
                                                            stderr=stderr_pipe)
        try:
            output, err = await asyncio.wait_for(proc_handle.communicate(), timeout=self._simc_timeout)
        except asyncio.TimeoutError:
            # HecticAddCleave can take a long time on some specs -- make the timeout generous to avoid skipping any
            logger.error("Sim timed out with string %s, skipping." % sim_string)

            proc_handle.kill()
            await proc_handle.communicate()

            raise

        if err is not None:
            logger.error("Simcraft error '%s'" % str(err))

            raise SimulationcraftProcessError(str(err))

        cleaned_output = output.decode('utf-8').replace('\r', '').replace('\n', '')
        return int(self.find_dps(cleaned_output))

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

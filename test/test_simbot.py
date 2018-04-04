import unittest

from src.simbot import SimBotConfig, SimcraftBot


class TestSimcraftBot(unittest.TestCase):
    def setUp(self):
        sbc = SimBotConfig()
        sbc.init_args("Clutch", "Fizzcrank",
                      "C:\\Users\\reedt\Downloads\\simc-715-02-win64-bdd3ba8\\simc-715-02-win64\\simc.exe",
                      write_logs=False)

        self.sb = SimcraftBot(sbc)

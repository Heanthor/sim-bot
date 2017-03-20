# coding=utf-8
# PyCharm workaround
from __future__ import absolute_import

import unittest

from src.api.warcraftlogs import WarcraftLogsError
from src.simbot import SimcraftBot


class TestSimcraftBot(unittest.TestCase):
    def setUp(self):
        self.sb = SimcraftBot("Clutch", "Fizzcrank", "US", "heroic", 3, 110,
                              "C:\\Users\\reedt\Downloads\\simc-715-02-win64-bdd3ba8\\simc-715-02-win64\\simc.exe", 15)

    def testSimReports(self):
        self.assertIsNone(self.sb.sim_single_character("Heanthor", "Fizzcrank")["error"])
        self.assertIsNone(self.sb.sim_single_character("Råekwon", "Fizzcrank")["error"])
        # caused errors on HecticAddCleave
        self.assertIsNone(self.sb.sim_single_character("Thanaton", "Fizzcrank")["error"])
        # has had empty response
        self.assertEqual(self.sb.sim_single_character("Thugy", "Fizzcrank")["error"], WarcraftLogsError.NO_RECENT_KILLS)

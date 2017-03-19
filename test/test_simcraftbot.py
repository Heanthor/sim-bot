# coding=utf-8
# PyCharm workaround
from __future__ import absolute_import

import unittest

from src.simbot import SimcraftBot


class TestSimcraftBot(unittest.TestCase):
    def setUp(self):
        self.sb = SimcraftBot("Clutch", "Fizzcrank", "US", "heroic", 3, 110,
                              "C:\\Users\\reedt\Downloads\\simc-715-02-win64-bdd3ba8\\simc-715-02-win64\\simc.exe", 10)

    def testSimReports(self):
        # self.assertTrue(self.sb.sim_single_character("Heanthor", "Fizzcrank"))
        self.assertTrue(self.sb.sim_single_character("Råekwon", "Fizzcrank"))
        # caused errors on HecticAddCleave
        # self.assertTrue(self.sb.sim_single_character("Thanaton", "Fizzcrank"))

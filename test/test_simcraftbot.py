# PyCharm workaround
from __future__ import absolute_import

import unittest

from src.main import SimcraftBot


class TestSimcraftBot(unittest.TestCase):
    def setUp(self):
        self.sb = SimcraftBot("Clutch", "Fizzcrank", "US", "heroic", 3, 110,
                              "C:\\Users\\reedt\Downloads\\simc-715-02-win64-92af786\\simc-715-02-win64\\simc.exe")

    def testSimReports(self):
        self.assertIsNotNone(self.sb.sim_single_character("Heanthor", "Fizzcrank"))

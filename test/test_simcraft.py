# PyCharm workaround
from __future__ import absolute_import

import json
import unittest

from src.api.simcraft import SimulationCraft

with open("dps_out_1.txt", 'r') as f:
    dps_str_1 = f.read()

with open("dps_out_2.txt", 'r') as f:
    dps_str_2 = f.read()


class TestSimcraft(unittest.TestCase):
    def test_find_dps(self):
        self.assertEqual('845266', SimulationCraft.find_dps(dps_str_1))
        self.assertEqual('1109791', SimulationCraft.find_dps(dps_str_2))

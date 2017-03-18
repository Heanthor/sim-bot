# PyCharm workaround
from __future__ import absolute_import

import json
import unittest

from src.api.warcraftlogs import WarcraftLogs
from src.data_structures.warcraftlogs import ParseResponse

with open("sample_warcraftlogs_api_response.json", 'r') as f:
    api_stub = json.loads(f.read())

with open("7_1_5_talents.json", 'r') as f:
    talent_dump = json.loads(f.read())


class TestWarcraftLogs(unittest.TestCase):
    def test_convert_talents(self):
        mage_talents = [
            {
                "name": "Ray of Frost",
                "id": 205021
            },
            {
                "name": "Shimmer",
                "id": 212653
            },
            {
                "name": "Incanter's Flow",
                "id": 1463
            },
            {
                "name": "Splitting Ice",
                "id": 56377
            },
            {
                "name": "Frigid Winds",
                "id": 235224
            },
            {
                "name": "Unstable Magic",
                "id": 157976
            },
            {
                "name": "Thermal Void",
                "id": 155149
            }
        ]

        demonhunter_talents = [
            {
                "name": "Fel Mastery",
                "id": 192939
            },
            {
                "name": "Prepared",
                "id": 203551
            },
            {
                "name": "Bloodlet",
                "id": 206473
            },
            {
                "name": "Soul Rending",
                "id": 204909
            },
            {
                "name": "Momentum",
                "id": 206476
            },
            {
                "name": "Unleashed Power",
                "id": 206477
            },
            {
                "name": "Demonic",
                "id": 213410
            }
        ]

        self.assertEqual([0, 0, 2, 2, 0, 1, 0],
                         WarcraftLogs.convert_talents("Mage", "Frost", mage_talents, talent_dump))

        self.assertEqual([0, 0, 2, 2, 0, 1, 2],
                         WarcraftLogs.convert_talents("DemonHunter", "Havoc", demonhunter_talents, talent_dump))

    def test_process_parse(self):


class TestParseResponse(unittest.TestCase):
    def setUp(self):
        self.pr = ParseResponse(api_stub)

    def test_filter_kills(self):
        self.assertTrue(self.pr.filter_kills(21, self.pr.HEROIC))
        self.assertFalse(self.pr.filter_kills(21, "asdf"))
        self.assertFalse(self.pr.filter_kills(0, self.pr.NORMAL))


if __name__ == '__main__':
    unittest.main()

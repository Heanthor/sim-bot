# PyCharm workaround
from __future__ import absolute_import

import json
import unittest

from src.api.warcraftlogs import WarcraftLogs

with open("sample_warcraftlogs_api_response.json", 'r') as f:
    api_stub = json.loads(f.read())

with open("7_1_5_talents.json", 'r') as f:
    talent_dump = json.loads(f.read())


class TestWarcraftLogs(unittest.TestCase):
    def setUp(self):
        self.wl = WarcraftLogs("")
        self.wl.set_talent_data(talent_dump)

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

        self.assertEqual([1, 1, 3, 3, 1, 2, 1],
                         self.wl.convert_talents("Mage", "Frost", mage_talents))

        self.assertEqual([1, 1, 3, 3, 1, 2, 3],
                         self.wl.convert_talents("DemonHunter", "Havoc", demonhunter_talents))

    def test_process_parse(self):
        # 999 weeks to prevent breaking dataset
        result = self.wl.process_parses("Stachio", 4, 999, api_stub, talent_dump)

        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()

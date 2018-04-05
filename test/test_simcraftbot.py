# coding=utf-8
# PyCharm workaround
from __future__ import absolute_import

import json
import os
import unittest

from src.api.simcraft import SimulationCraft
from src.simbot import SimcraftBot, SimBotConfig
from test.mocks.battlenet_mock import BattleNetMock
from test.mocks.warcraftlogs_mock import WarcraftLogsMock


class TestSimcraftBot(unittest.TestCase):
    def setUp(self):
        sbc = SimBotConfig()
        sbc.init_args("TestGuild_NoAPI", "TestRealm_NoAPI",
                      "C:\\Users\\reedt\\Downloads\\simc-735-01-win64\\simc-735-01-win64\\simc.exe",
                      config_path='../config',
                      write_logs=False)

        # load json dumps
        # NOTE: player name order matters here
        # since the warcraftlogs mock doesn't dumbly returns the next group of logs each call
        # the order players are returned must match the order they appear in the bnet dump of the guild
        # empty responses match players with no logs returned by bnet
        player_names = ["Redrimer"] + ["empty"] * 6 + ["Lunaraura"] + ["empty"] * 7 + ["Verrota"]
        warcr_entries = []
        with open('bnet_guild.json', 'rb') as f:
            bnet_guild = f.read().decode('utf-8')

        with open('bnet_talent.json', 'rb') as f:
            bnet_talent = f.read().decode('utf-8')

        for name in player_names:
            with open('warcr_%s.json' % name, 'rb') as f:
                warcr_entries.append(f.read().decode('utf-8'))

        with open(os.path.join(sbc.params["config_path"], "boss_profiles.json"), 'r') as f:
            profiles = json.loads(f.read())

        # create mock objects to standardize api responses
        bnet = BattleNetMock(bnet_guild, bnet_talent)
        warcr = WarcraftLogsMock('{}', warcr_entries)
        simc = SimulationCraft(sbc.params["simc_location"], sbc.params["simcraft_timeout"], sbc.params["config_path"])

        self.sb = SimcraftBot(sbc, bnet, warcr, simc, profiles)

    def testSimReports(self):
        self.sb.run_all_sims()

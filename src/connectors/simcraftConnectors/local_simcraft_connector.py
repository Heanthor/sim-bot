import asyncio

import sys

from src.connectors.simcraftConnectors.simcraft_connector import SimcraftConnector


# noinspection PyCompatibility
class LocalSimcraftConnector(SimcraftConnector):
    def __init__(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop(asyncio.ProactorEventLoop())

        self.loop = asyncio.get_event_loop()
        self.running_sims = []

    def queue_sim(self, sim_coro, *args, **kwargs):
        self.running_sims.append(sim_coro(*args, **kwargs))

    def get_completed_sims(self):
        try:
            # blocks until complete
            results = self.loop.run_until_complete(asyncio.gather(*self.running_sims))

            return results
        finally:
            self.loop.close()
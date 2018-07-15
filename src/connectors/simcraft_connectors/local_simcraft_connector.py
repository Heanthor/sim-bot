import asyncio

import sys

from src.connectors.simcraft_connectors.simcraft_connector import SimcraftConnector


# noinspection PyCompatibility
class LocalSimcraftConnector(SimcraftConnector):
    def __init__(self):
        super().__init__()

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

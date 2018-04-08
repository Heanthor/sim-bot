import asyncio

from src.connectors.simcraftConnectors.simcraft_connector import SimcraftConnector


# noinspection PyCompatibility
class LocalSimcraftConnector(SimcraftConnector):
    def __init__(self):
        self.running_sims = []

    def queue_sim(self, sim_func, *args, **kwargs):
        self.running_sims.append(sim_func(args, kwargs))

    async def _block_all_sims(self):
        return await asyncio.wait(self.running_sims)

    def get_completed_sims(self):
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self._block_all_sims())

        finally:
            loop.close()

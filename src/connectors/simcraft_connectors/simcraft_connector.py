import sys

import asyncio


class SimcraftConnector:
    def __init__(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop(asyncio.ProactorEventLoop())

    def queue_sim(self, sim_func, *args, **kwargs):
        pass

    def get_completed_sims(self):
        """
        Blocks until all queued sims are complete
        :return: List of data from completed sims
        """
        pass

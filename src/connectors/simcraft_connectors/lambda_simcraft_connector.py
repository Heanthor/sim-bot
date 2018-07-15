import aiohttp
import asyncio

from src.connectors.simcraft_connectors.simcraft_connector import SimcraftConnector


class LambdaSimcraftConnector(SimcraftConnector):
    def __init__(self, urls):
        super().__init__()

        # note, not a proactor event loop (overrides super)
        self._old_loop = asyncio.get_event_loop()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.sim_args = []
        self._urls = urls

    @staticmethod
    async def fetch(player, session, url, data):
        async with session.post(url, json=data) as response:
            if response.status != 200:
                simc_response = {
                    "player_name": player,
                    "error": await response.json()
                }

                return simc_response

            return await response.json()

    async def call_lambda(self, session, player, realm_slug, region, iterations, raiding_stats):
        request_body = {
            "sim_params": {
                "character_name": player,
                "realm_slug": realm_slug,
                "region": region,
                "iterations": iterations,
                "raiding_stats": raiding_stats
            }
        }
        resp = await self.fetch(player, session, self._urls["lambda"]["production"], request_body)

        print(resp)

        return resp

        # TODO notify of completion here

    def queue_sim(self, sim_coro, *args, **kwargs):
        self.sim_args.append(args)

    async def _run(self):
        tasks = []

        async with aiohttp.ClientSession() as session:
            for args in self.sim_args:
                task = asyncio.ensure_future(self.call_lambda(session, *args))
                tasks.append(task)

            return await asyncio.gather(*tasks)

    def get_completed_sims(self):
        try:
            future = asyncio.ensure_future(self._run())

            # blocks until complete
            raw = self.loop.run_until_complete(future)

            return [x["suite"] for x in raw]
        finally:
            self.loop.close()
            asyncio.set_event_loop(self._old_loop)

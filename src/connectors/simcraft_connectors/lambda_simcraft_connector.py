import aiohttp

from src.connectors.simcraft_connectors.simcraft_connector import SimcraftConnector


class LambdaSimcraftConnector(SimcraftConnector):
    def __init__(self, simbot):
        self._simbot = simbot
        self.running_sims = []
        self.session = aiohttp.ClientSession()

    @staticmethod
    async def fetch(session, url, data):
        async with session.post(url, json=data) as response:
            return await response.text()

    async def call_lambda(self, player, realm_slug, region, iterations, raiding_stats):
        request_body = {
            "player": player,
            "realm_slug": realm_slug,
            "region": region,
            iterations: iterations,
            "raiding_stats": raiding_stats
        }
        html = await self.fetch(self.session, 'http://python.org', request_body)
        # TODO notify of completion here
        print(html)

    def queue_sim(self, sim_coro, *args, **kwargs):
        self.running_sims.append(self.call_lambda(*args))

from src.api.battlenet import BattleNet


# noinspection PyCompatibility
from test.mocks.request_mock import RequestMock


class BattleNetMock(BattleNet):
    def __init__(self, guild_response, talent_response):
        super().__init__("")

        self.guild_response = guild_response
        self.talent_response = talent_response

    def bnet_request(self, req_func, *args, **kwargs):
        """
        Mock API call with provided response instead
        Check the API call by inspecting the URL passed as first arg
        """

        url = args[0]

        if "guild" in url:
            return RequestMock(self.guild_response)
        elif "talents" in url:
            return RequestMock(self.talent_response)
        else:
            raise Exception("Unable to mock endpoint %s" % url)
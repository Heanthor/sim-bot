from src.api.battlenet import BattleNet


# noinspection PyCompatibility
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

        # approximate a Requests response object
        def ret_obj(data_in):
            def json():
                return data_in

            def status_code():
                return 200

        if "guild" in url:
            return ret_obj(self.guild_response)
        elif "talents" in url:
            return ret_obj(self.talent_response)
        else:
            raise Exception("Unable to mock endpoint %s" % url)
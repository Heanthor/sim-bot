from src.api.battlenet import BattleNet


# noinspection PyCompatibility
class BattleNetMock(BattleNet):
    def __init__(self):
        super().__init__("")
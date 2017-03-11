import json

from requests_oauthlib import OAuth2Session

from api.battlenet import BattleNet
from api.wowprogress import WarcraftLogs
from oauthlib.oauth2 import BackendApplicationClient


def main():
    with open("keys.json", 'r') as f:
        f = json.loads(f.read())
        warcraft_logs_public = f["warcraftlogs"]["public"]

    w = WarcraftLogs(warcraft_logs_public)
    print w.get_all_parses("Heanthor", "fizzcrank", "US", "dps")


def battlenet_test():
    with open("keys.json", 'r') as f:
        f = json.loads(f.read())
        battlenet_pub = f["battlenet"]["public"]
        battlenet_sec = f["battlenet"]["secret"]

    b = BattleNet(battlenet_pub)
    print b.get_guild_members("Fizzcrank", "Clutch", "en_US")
    # client = BackendApplicationClient(client_id=battlenet_pub)
    # oauth = OAuth2Session(client=client)
    # token = oauth.fetch_token(token_url='https://us.battle.net/oauth/token', client_id=battlenet_pub,
    #                           client_secret=battlenet_sec)


if __name__ == '__main__':
    battlenet_test()

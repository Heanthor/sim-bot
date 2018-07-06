import asyncio
import json
from asyncio import get_event_loop

import sys

from src.api.simcraft import SimulationCraft


def lambda_handler(event, context):
    sc = SimulationCraft("./simc", 5, "")
    body = json.loads(event["body"])

    loop = get_event_loop()
    promise = sc.run_sim(body["param_list"])

    dps = loop.run_until_complete(promise)

    loop.close()
    return dps

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    evt_dict = {
        "body":  json.dumps({
            "param_list": ["armory=US,Arthas,Heanthoro", "spec=enhancement", "talents=1211231", "iterations=100"]
        })
    }

    dps = lambda_handler(evt_dict, "")
    print(dps)


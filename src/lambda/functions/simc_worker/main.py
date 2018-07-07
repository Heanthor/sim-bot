import asyncio
import json
import os
from asyncio import get_event_loop

import sys

from src.api.simcraft import SimulationCraft


def response(message, status_code):
    return {
        'statusCode': int(status_code),
        'body': json.dumps(message),
        'isBase64Encoded': 'false',
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }


def handle(event, context):
    os.environ['PATH'] = os.environ['PATH'] + ':' + os.environ['LAMBDA_TASK_ROOT']

    sc = SimulationCraft("./lib/simc", 5, "")
    try:
        body = json.loads(event["body"])
        params = body["sim_params"]
    except Exception:
        return response({"error": "Invalid parameters provided"}, 500)

    loop = get_event_loop()
    promise = sc.run_sim(
        params["character_name"],
        params["realm_slug"],
        params["region"],
        params["spec"],
        params["talent_string"],
        params["iterations"]
    )

    try:
        dps = loop.run_until_complete(promise)
        return response({"dps": dps}, 200)
    except Exception as e:
        return response({"error": str(e)}, 500)


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    evt_dict = {
        "body": json.dumps({
            "param_list": ["armory=US,Arthas,Heanthoro", "spec=enhancement", "talents=1211231", "iterations=100"]
        })
    }

    dps = handle(evt_dict, "")
    print(dps)

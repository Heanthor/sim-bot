import asyncio
import json
import os
import traceback
from asyncio import get_event_loop

import sys

import boto3
import botocore

from src.api.simcraft import SimulationCraft
from src.simbot import SimcraftBot
from src.simbot_config import SimBotConfig

BUCKET_NAME = 'heanthor-simbot'  # replace with your bucket name
KEY = 'boss_profiles.json'  # replace with your object key
LOCAL_FILENAME = '/tmp/boss_profiles.json'

s3 = boto3.resource('s3')


def get_profiles():
    try:
        s3.Bucket(BUCKET_NAME).download_file(KEY, LOCAL_FILENAME)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


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
    os.environ['PATH'] = os.environ['PATH'] + ':' + os.getenv('LAMBDA_TASK_ROOT', '')

    try:
        body = json.loads(event["body"])
        params = body["sim_params"]
    except Exception:
        return response({"error": "Invalid parameters provided"}, 500)

    if not os.path.exists(LOCAL_FILENAME):
        # grab profiles from s3
        get_profiles()

    with open(LOCAL_FILENAME, 'r') as f:
        profile_dict = json.loads(f.read())

    sbc = SimBotConfig()
    sbc.init_args(
        "",
        params["realm_slug"],
        "./lib/simc",
        True,  # the sim is "local" on lambda
        simc_iter=params["iterations"],
        write_logs=False
    )

    sc = SimulationCraft("./lib/simc", 5, "/tmp")
    sb = SimcraftBot(sbc, None, None, sc, profile_dict)

    loop = get_event_loop()
    promise = sb.sim_single_suite(
        params["character_name"],
        params["realm_slug"],
        params["raiding_stats"]
    )

    try:
        suite = loop.run_until_complete(promise)
        return response({"suite": suite}, 200)
    except Exception as e:
        print(traceback.format_exc())
        return response({"error": str(e)}, 500)


if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    with open("../../../../test/raiding_stats_redrimer.json", 'r') as f:
        stats = json.loads(f.read())

    evt_dict = {
        "body": json.dumps({
            "sim_params": {
                "character_name": "Redrimer",
                "iterations": 100,
                "realm_slug": "Arthas",
                "region": "US",
                "raiding_stats": stats
            }
        })
    }

    dps = handle(evt_dict, "")
    print(dps)

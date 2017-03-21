import json

from flask import Flask
from flask import render_template, request
from flask_socketio import SocketIO

from src.simbot import SimBotConfig

app = Flask(__name__)
socketio = SocketIO(app)

with open('simbot_params.json', 'r') as f:
    saved_params = json.loads(f.read())


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/all_sims/", methods=["GET"])
def all_sims():
    region = request.args.get('region')
    difficulty = request.args.get('difficulty')
    weeks = request.args.get('weeks')
    guild = request.args.get('guild')
    realm = request.args.get('region')

    sbc = SimBotConfig()
    sbc.init_args(guild, realm, saved_params["simc_location"], saved_params["simc_timeout"], region, difficulty,
                  weeks_to_examine=weeks, log_path=saved_params["log_path"])
    return "All Sims!"


@app.route("/sim/", methods=["GET"])
def sim_single():
    # TODO simbot needs to be able to run without a guild param for this endpoint
    pass


@socketio.on('my event')
def handle_my_custom_event(j):
    print('received json: ' + str(j))


if __name__ == "__main__":
    socketio.run(app)

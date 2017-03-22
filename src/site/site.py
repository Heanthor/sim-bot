import threading

from flask import json, jsonify

from flask import Flask
from flask import render_template, request
from flask_socketio import SocketIO, emit

from src.simbot import SimBotConfig, SimcraftBot

# import eventlet
# eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

with open('simbot_params.json', 'r') as f:
    saved_params = json.loads(f.read())


# thread target
def check_sim_status(queue):
    while True:
        # print("Eventlet thread started")
        message = queue.get()
        print("MESSAGE IN SITE: " + str(message))
        # with app.app_context():
        #     socketio.emit("progressbar", json.dumps(message))
        socketio.emit("progressbar", json.dumps(message))

        queue.task_done()


# def report_sim_update(message):
#     print("MESSAGE IN SITE: " + str(message))
#     with app.app_context():
#         socketio.emit("progressbar", json.dumps(message))


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/all_sims/", methods=["GET"])
def all_sims():
    region = request.args.get('region')
    difficulty = request.args.get('difficulty')
    weeks = request.args.get('weeks')
    guild = request.args.get('guild')
    realm = request.args.get('realm')

    sbc = SimBotConfig()
    sbc.init_args(guild, realm, saved_params["simc_location"], saved_params["config_path"],
                  saved_params["simc_timeout"], region, difficulty, weeks_to_examine=weeks,
                  log_path=saved_params["log_path"])

    sb = SimcraftBot(sbc)

    t = threading.Thread(target=check_sim_status, args=(sb.event_queue,), daemon=True)
    t.start()
    # eventlet.spawn(check_sim_status, sb.event_queue)
    # sb.register_alert_func(report_sim_update)

    report = sb.run_all_sims()
    return jsonify(report)


@app.route("/sim/", methods=["GET"])
def sim_single():
    pass


@socketio.on('my event')
def handle_my_custom_event(j):
    print('received json: ' + str(j))
    # emit('progressbar', "hello back")


if __name__ == "__main__":
    socketio.run(app, debug=True)

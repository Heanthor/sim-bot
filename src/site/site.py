import threading

import time

from flask import json, jsonify

from flask import Flask
from flask import render_template, request
from flask_socketio import SocketIO

from src.simbot import SimBotConfig, SimcraftBot

from multiprocessing.pool import ThreadPool

import logging

# import eventlet
# eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)
logger = logging.getLogger("SimBot")


# Taiiwo @ https://gist.github.com/ericremoreynolds/dbea9361a97179379f3b#gistcomment-1730314
class Socket:
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

    # Emits data to a socket's unique room
    def emit(self, event, data):
        socketio.emit(event, data, room=self.sid)


# currently connected socket.io clients
sockets = {}
# client ID to socket SID
client_socket = {}
# reference to SimcraftBot objects
all_running_jobs = {}

with open('simbot_params.json', 'r') as f:
    saved_params = json.loads(f.read())


# thread target
def check_sim_status(queue, client_id):
    with app.test_request_context():
        while True:
            # print("Eventlet thread started")
            message = queue.get()
            print("MESSAGE IN SITE: " + str(message))
            # with app.app_context():
            #     socketio.emit("progressbar", json.dumps(message))
            # send message to correct client
            client_socket[client_id].emit("progressbar", message)
            queue.task_done()


# def report_sim_update(message):
#     print("MESSAGE IN SITE: " + str(message))
#     with app.app_context():
#         socketio.emit("progressbar", json.dumps(message))


# thread to check task progress.
# cycle through all running tasks, query their status
# if ready, send a socketio message to that client, along with the data
def check_task_progress():
    logger.debug("Task progress thread started")

    with app.test_request_context():
        while True:
            for client_id, (task, simbot_obj) in list(all_running_jobs.items()):
                if task.ready():
                    sock = client_socket[client_id]

                    try:
                        result = task.get()

                        sock.emit("guild-result", {
                            "status": "success",
                            "message": "Sim complete",
                            "data": result  # result is a dict
                        })
                    except Exception as e:
                        # error
                        sock.emit("guild-result", {
                            "status": "error",
                            "message": str(e)
                        })

                        # task is dead now
                        del all_running_jobs[client_id]
            # can tune this for faster response
            time.sleep(0.1)


@app.route("/")
def main():
    return render_template("main.html")


pool = ThreadPool(processes=1)


@app.route("/all_sims/", methods=["POST"])
def all_sims():
    job_id = request.form.get('jobID')

    if job_id in all_running_jobs:
        return jsonify({
            "status": "error",
            "message": "Job already started."
        })

    region = request.form.get('region')
    difficulty = request.form.get('difficulty')
    weeks = request.form.get('weeks')
    guild = request.form.get('guild')
    realm = request.form.get('realm')

    sbc = SimBotConfig()
    sbc.init_args(guild, realm, saved_params["simc_location"], saved_params["config_path"],
                  saved_params["simc_timeout"], region, difficulty, weeks_to_examine=weeks,
                  log_path=saved_params["log_path"])

    sb = SimcraftBot(sbc)

    # TODO multiple jobs

    threading.Thread(target=check_sim_status, args=(sb.event_queue, job_id), daemon=True).start()

    # TODO return from this immediately, but keep the result going, send it back later
    async_result = pool.apply_async(sb.run_all_sims)
    all_running_jobs[job_id] = (async_result, sb)

    logger.debug("Queued task for client %s", job_id)
    # result = sb.run_all_sims()

    return jsonify({
        "status": "success",
        "message": "Task queued,"
    })


@app.route("/sim/", methods=["POST"])
def sim_single():
    pass


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id=None):
    job, simbot_obj = all_running_jobs[job_id]

    simbot_obj.cancelFlag = True
    print("Cancel! job %s" % job_id)

    return jsonify({
        "status": "success",
        "message": "Job cancelled."
    })


@socketio.on('connect')
def client_connected():
    sockets[request.sid] = Socket(request.sid)
    print("Client connected")


@socketio.on('handshake')
def handshake_client(data):
    client_socket[data['data']] = sockets[request.sid]


if __name__ == "__main__":
    SimBotConfig.init_logger(False, saved_params["log_path"])

    # task response thread
    threading.Thread(target=check_task_progress).start()
    socketio.run(app, debug=True)

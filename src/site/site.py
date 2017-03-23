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

# reference to SimcraftBot objects
all_running_jobs = {}

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


@app.route("/all_sims/", methods=["POST"])
def all_sims():
    job_id = request.form.get('jobID')

    if job_id in all_running_jobs:
        return jsonify({
            "status": "error",
            "message": "Job already started."
        }), 400

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
    try:
        all_running_jobs[job_id] = sb

        t = threading.Thread(target=check_sim_status, args=(sb.event_queue,), daemon=True)
        t.start()
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    # eventlet.spawn(check_sim_status, sb.event_queue)
    # sb.register_alert_func(report_sim_update)

    report = sb.run_all_sims()
    return jsonify(report)


@app.route("/sim/", methods=["GET"])
def sim_single():
    pass


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id=None):
    job = all_running_jobs[job_id]

    del job
    print("Cancel! job %s" % job_id)

    return jsonify({
        "status": "success",
        "message": "Job cancelled."
    })


@socketio.on('my event')
def handle_my_custom_event(j):
    print('received json: ' + str(j))
    # emit('progressbar', "hello back")


if __name__ == "__main__":
    socketio.run(app, debug=True)

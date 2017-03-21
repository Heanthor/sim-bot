from flask import Flask
from flask import render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/all_sims/", methods=["GET"])
def all_sims():
    pass


@app.route("/sim/", methods=["GET"])
def sim_single():
    # TODO simbot needs to be able to run without a guild param for this endpoint
    pass


if __name__ == "__main__":
    socketio.run(app)

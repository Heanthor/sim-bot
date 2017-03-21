from flask import Flask
from flask import render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/all_sims/<guild>/<realm>/<locale>/<num_weeks>")
def all_sims(guild=None, realm=None, locale=None, num_weeks=None):
    pass


@app.route("/sim/<name>/<realm>/<locale>/<num_weeks>")
def sim_single(name=None, realm=None, locale=None, num_weeks=None):
    pass


if __name__ == "__main__":
    socketio.run(app)

from flask import Flask
from flask import render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def main():
    return render_template("main.html")

#def all_sims("/all_sims/<")





if __name__ == "__main__":
    socketio.run(app)

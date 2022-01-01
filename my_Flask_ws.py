"""
File: chapter03/flask_ws_server.py

A Flask based Web Sockets server to control an LED built using Flask-SocketIO.

Dependencies:
  pip3 install gpiozero pigpio flask-socketio

Built and tested with Python 3.7 on Raspberry Pi 4 Model B
"""
import logging
import threading
from typing import Dict

from flask import Flask, request, render_template
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import time
import pigpio

# Initialize Logging
logging.basicConfig(level=logging.WARNING)  # Global logging configuration
logger = logging.getLogger('main')  # Logger for this module
logger.setLevel(logging.INFO)  # Debugging for this file.

# Creating an instance of pigpio
pi = pigpio.pi()

# Flask & Flask Restful Global Variables.
app = Flask(__name__)  # Core Flask app.
socketio = SocketIO(app)  # Flask-SocketIO extension wrapper.

# Global variables
is_blinking = False
mainRoom = {'room': "1153"}
sideRoom = {'room': "1154"}
initialized = False
# Main street traffic light pins
MAIN_RED_PIN = 21
MAIN_GREEN_PIN = 20
# Side street traffic light pins
SIDE_RED_PIN = 5
SIDE_GREEN_PIN = 6

"""
GPIO Related Functions
"""


def initializeLEDS():
    pi.write(MAIN_RED_PIN, 1)
    pi.write(SIDE_RED_PIN, 0)
    pi.write(MAIN_GREEN_PIN, 0)
    pi.write(SIDE_GREEN_PIN, 1)


"""
Flask & Flask-SocketIO Related Functions
"""


# @app.route apply to the raw Flask instance.
# Here we are serving a simple web page.
@app.route('/', methods=['GET'])
def index():
    global initialized
    if initialized == False:
        initialized = True
        socketio.emit('blink', mainRoom)
        socketio.emit('blink', sideRoom)
    return render_template('Flask_WS_TrafficLights.html', pin=[MAIN_RED_PIN, SIDE_RED_PIN])


# Flask-SocketIO Callback Handlers
@socketio.on('connect')
def handle_connect():
    """Called when a remote web socket client connects to this server"""
    logger.info("Client {} connected.".format(request.sid))


@socketio.on('disconnect')
def handle_disconnect():
    """Called with a client disconnects from this server"""
    logger.info("Client {} disconnected.".format(request.sid))


@socketio.on('join')
def joinRoom(data):
    plateNo = data['plateNo']
    room = data['room']
    join_room(room)
    logger.info(plateNo + " is coming to the " + data['destination'] + " joined room :" + room)
    # Send to traffic in the room that a car is coming from main or side streets
    socketio.send(plateNo + "  is coming to the " + data['destination'], to=room, include_self = False)


@socketio.on('leave')
def joinRoom(data):
    plateNo = data['plateNo']
    room = data['room']
    leave_room(room)
    # Send to traffic in the room that a car has left from main or side streets
    socketio.send(plateNo + " is leaving the " + data['destination'], to=room, include_self=False)

@socketio.on('message')
def handle_message(msg):
    logger.info(msg)
    payload = {'message' : msg}
    socketio.emit('message', payload)

@socketio.on('pedestrian')
def handle_state():
    """Handle messages to control the trafficLight when a pedestrian crosses."""
    global is_blinking
    is_blinking = False
    pi.write(MAIN_RED_PIN, 1)
    pi.write(SIDE_RED_PIN, 1)
    pi.write(MAIN_GREEN_PIN, 0)
    pi.write(SIDE_GREEN_PIN, 0)
    # Send a message to all traffic
    socketio.send("A pedestrian is crossing", to=mainRoom['room'], include_self=False)
    socketio.send("A pedestrian is crossing", to=sideRoom['room'], include_self=False)
    time.sleep(7)
    emit('blink', sideRoom)
    emit('blink', mainRoom)

@socketio.on('blink')
def blink(data):
    global is_blinking

    is_blinking = True
    room = data['room']
    def do_blink():
        while is_blinking:
            time.sleep(3)
            if room == "1154":
                pi.write(SIDE_RED_PIN, 0)
                pi.write(SIDE_GREEN_PIN, 1)
                socketio.send("Side street traffic light is red", to=room)
            elif room == "1153":
                pi.write(MAIN_RED_PIN, 1)
                pi.write(MAIN_GREEN_PIN, 0)
                socketio.send("Main street traffic light is red", to=room)

            time.sleep(3)
            if is_blinking:
                if room == "1154":
                    pi.write(SIDE_RED_PIN, 1)
                    pi.write(SIDE_GREEN_PIN, 0)
                    socketio.send("Side street traffic light is green", to=room)
                elif room == "1153":
                    pi.write(MAIN_RED_PIN, 0)
                    pi.write(MAIN_GREEN_PIN, 1)
                    socketio.send("Main street traffic light is green", to=room)

    # daemon=True prevents our thread below from preventing the main thread
    # (essentially the code in if __name__ == '__main__') from exiting naturally
    # when it reaches it's end. If you try daemon=False you will discover that the
    # program never quits back to the Terminal and appears to hang after the LED turns off.
    thread = threading.Thread(name='current room is ' + str(room), target=do_blink, daemon=True)
    thread.start()


# Initialize LEDS
initializeLEDS()

if __name__ == '__main__':

    socketio.run(app, host='0.0.0.0', debug=True)


import logging
from flask import Flask, request, render_template
from flask_restful import Resource, Api, reqparse, inputs
import pigpio
from gpiozero.pins.pigpio import PiGPIOFactory
import time
import threading
import requests

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

# Creating an instance of pigpio
pi = pigpio.pi()

# Initialize flask to use this module so it can find template and static files
app = Flask(__name__)
# Initialize the Flask restefull extention wrapper
api = Api(app)

# Global variables
GREEN = False
RED = True
is_blinking = False
# Main street traffic light pins
MAIN_RED_PIN = 21
MAIN_GREEN_PIN = 20
MAIN_STREET_RED_LIGHT_STATE = GREEN
# Side street traffic light pins
SIDE_RED_PIN = 5
SIDE_GREEN_PIN = 6
SIDE_STREET_RED_LIGHT_STATE = RED


def setLEDS():
    pi.write(MAIN_RED_PIN, MAIN_STREET_RED_LIGHT_STATE)
    pi.write(SIDE_RED_PIN, SIDE_STREET_RED_LIGHT_STATE)
    pi.write(MAIN_GREEN_PIN, not MAIN_STREET_RED_LIGHT_STATE)
    pi.write(SIDE_GREEN_PIN, not SIDE_STREET_RED_LIGHT_STATE)


@app.route('/', methods=['GET'])
def index():
    return render_template('Flask_Restfull_TrafficLights.html', pin=[MAIN_RED_PIN, SIDE_RED_PIN])


class sideTraffic(Resource):
    def __init__(self):
        self.args = reqparse.RequestParser()
        self.args.add_argument(
            name='sideLED',
            required=True,
            type=inputs.boolean,
            help='side led {error_msg}',
            default=None
        )

    def get(self):
        global SIDE_STREET_RED_LIGHT_STATE
        jason = {'sideLED': SIDE_STREET_RED_LIGHT_STATE}
        return jason

    def post(self):
        global SIDE_STREET_RED_LIGHT_STATE
        jason = {'sideLED': SIDE_STREET_RED_LIGHT_STATE}
        return jason


api.add_resource(sideTraffic, '/sideTraffic')


class mainTraffic(Resource):
    def __init__(self):
        self.args = reqparse.RequestParser()
        self.args.add_argument(
            name='mainLED',
            required=True,
            type=inputs.boolean,
            help='main led {error_msg}',
            default=None
        )

    def get(self):
        global MAIN_STREET_RED_LIGHT_STATE
        jason = {'mainLED': MAIN_STREET_RED_LIGHT_STATE}
        return jason

    def post(self):
        global MIAN_LED_STATE
        jason = {'mainLED': MAIN_STREET_RED_LIGHT_STATE}
        return jason


api.add_resource(mainTraffic, '/mainTraffic')


class pedestrian(Resource):
    def __init__(self):
        self.args = reqparse.RequestParser()
        self.args.add_argument(
            name='mainLED',
            required=True,
            type=inputs.boolean,
            help='main led {error_msg}',
            default=None
        )
        self.args.add_argument(
            name='sideLED',
            required=True,
            type=inputs.boolean,
            help='side led {error_msg}',
            default=None
        )

    def get(self):
        global SIDE_STREET_RED_LIGHT_STATE
        global MAIN_STREET_RED_LIGHT_STATE
        jason = {'mainLED': MAIN_STREET_RED_LIGHT_STATE, 'sideLED': SIDE_STREET_RED_LIGHT_STATE}
        return jason

    def post(self):
        global SIDE_STREET_RED_LIGHT_STATE
        global MAIN_STREET_RED_LIGHT_STATE
        global is_blinking
        is_blinking = False
        tempSide = SIDE_STREET_RED_LIGHT_STATE
        tempMain = MAIN_STREET_RED_LIGHT_STATE
        SIDE_STREET_RED_LIGHT_STATE = RED
        MAIN_STREET_RED_LIGHT_STATE = RED
        setLEDS()
        time.sleep(7)
        SIDE_STREET_RED_LIGHT_STATE = tempSide
        MAIN_STREET_RED_LIGHT_STATE = tempMain
        setLEDS()
        blink(SIDE_RED_PIN, SIDE_GREEN_PIN)
        blink(MAIN_RED_PIN, MAIN_GREEN_PIN)
        jason = {'mainLED': not MAIN_STREET_RED_LIGHT_STATE, 'sideLED': not SIDE_STREET_RED_LIGHT_STATE}
        return jason


api.add_resource(pedestrian, '/pedestrian')


def blink(red_pin, green_pin, background=True):
    global is_blinking
    global SIDE_STREET_RED_LIGHT_STATE
    global MAIN_STREET_RED_LIGHT_STATE

    is_blinking = True

    def do_blink():
        global SIDE_STREET_RED_LIGHT_STATE
        global MAIN_STREET_RED_LIGHT_STATE
        while is_blinking:
            time.sleep(3)
            if SIDE_RED_PIN == red_pin:
                pi.write(red_pin, 0)
                pi.write(green_pin, 1)
                SIDE_STREET_RED_LIGHT_STATE = GREEN
            # requests.post(url = (URL + "sideTraffic"))
            elif MAIN_RED_PIN == red_pin:
                pi.write(red_pin, 1)
                pi.write(green_pin, 0)
                MAIN_STREET_RED_LIGHT_STATE = RED
            # requests.post(url = (URL + "mainTraffic"))
            time.sleep(3)

            if SIDE_RED_PIN == red_pin:
                pi.write(red_pin, 1)
                pi.write(green_pin, 0)
                SIDE_STREET_RED_LIGHT_STATE = RED
            # requests.post(url = (URL + "sideTraffic"))
            elif MAIN_RED_PIN == red_pin:
                pi.write(red_pin, 0)
                pi.write(green_pin, 1)
                MAIN_STREET_RED_LIGHT_STATE = GREEN
            # requests.post(url = (URL + "mainTraffic"))

    if background:
        # daemon=True prevents our thread below from preventing the main thread
        # (essentially the code in if __name__ == '__main__') from exiting naturally
        # when it reaches it's end. If you try daemon=False you will discover that the
        # program never quits back to the Terminal and appears to hang after the LED turns off.
        thread = threading.Thread(name='LED on GPIO ' + str(red_pin),
                                  target=do_blink,
                                  daemon=True)
        thread.start()
    else:
        do_blink()  # Blocking.


# Initialize LEDS
setLEDS()

if __name__ == '__main__':
    blink(SIDE_RED_PIN, SIDE_GREEN_PIN)
    blink(MAIN_RED_PIN, MAIN_GREEN_PIN)
    app.run(host="0.0.0.0", debug=True)

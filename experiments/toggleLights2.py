#!/usr/bin/python

# A simple script to toggle an LED light using a pushbutton

from __future__ import division
import RPi.GPIO as GPIO
import json
import spidev
import threading
import time
import urllib2

KNOB_CHANNEL = 0
JITTER_TOLERANCE = 7

GREEN_LED_PIN = 11
BLUE_LED_PIN = 13
RED_LED_PIN = 15
SQUARE_LED_PIN = 18
BLUE_BUTTON_PIN = 10
RED_BUTTON_PIN = 8
SQUARE_BUTTON_PIN = 16

KNOB_MIN = 0
KNOB_MAX = 255
KNOB_MID = (KNOB_MIN + KNOB_MAX) / 2
BRIGHT_MIN = 0
BRIGHT_MAX = 254

BASE_URL = 'http://192.168.1.62/api/newdeveloper/lights'

CHECK_LIGHTS_SLEEP_TIME = 0.5
CHECK_BUTTON_SLEEP_TIME = 0.05
CHECK_KNOB_SLEEP_TIME = .05

SLOW_BLINK_TIME = .4
FAST_BLINK_TIME = .1
REALLY_FAST_BLINK_TIME = .05

LONG_PRESS_TIME = 2.0

# Indicates whether Hue lights are off.
lightsOff = True

# If true, then we let the blink routine override other LED updates
blinking = False

# Saved brightness
lastKnob = 0

# Map from light IDs to curves
lightToCurve = {}

# Representation of current scene
currentScene = []

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(SQUARE_LED_PIN, GPIO.OUT)
GPIO.setup(BLUE_BUTTON_PIN, GPIO.IN)
GPIO.setup(RED_BUTTON_PIN, GPIO.IN)
GPIO.setup(SQUARE_BUTTON_PIN, GPIO.IN)


def get(url):
    response = urllib2.urlopen(url)
    result = response.read()
    return result

def put(url, data):
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url, data=data)
    request.get_method = lambda: 'PUT'
    result = opener.open(request)

# Utility for timing a function.  Add @timing before a function to instrument it.
def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1) * 1000.0)
        return ret
    return wrap

def makeStateUrl(lightnum):
    return "%s/%d/state" % (BASE_URL, lightnum)

def computeBrightness(knobValue, coefficients):
    (a, b) = coefficients
    y = a * knobValue ** 2 + b * knobValue
    return max(0,int(y))

def computeBrightnessCurve(normalBrightness):
    """Given a normal brightness, return a tuple (a, b) for the coefficients of ax^2 + bx + c
    We assume c = 0, x is the knob, y is the brightness"""
    def b(a):
        num = BRIGHT_MAX - a * KNOB_MAX ** 2
        den = KNOB_MAX
        return num/den

    def a():
        num = normalBrightness - (BRIGHT_MAX * KNOB_MID) / KNOB_MAX
        den = KNOB_MID * (KNOB_MID - KNOB_MAX)
        return num/den

    a = a()
    b = b(a)
    return (a,b)

def computeBrightnessCurves():
    global lightToCurve
    jsonText = get(BASE_URL)
    lightsJson = json.loads(jsonText)
    for name, info in lightsJson.iteritems():
        state = info['state']
        bri = state['bri']
        coeff = computeBrightnessCurve(bri)
        lightToCurve[name] = coeff
    return True

def allLightsAreOff(lightsJson):
    for name, info in lightsJson.iteritems():
        state = info['state']
        on = state['on']
        if on:
            return False
    return True

def lightOn(light):
    url = makeStateUrl(light)
    data = "{\"on\": true}"
    put(url, data)

def lightOff(light):
    url = makeStateUrl(light)
    data = "{\"on\": false}"
    put(url, data)

def allOn():
  for light in range(1,13):
    lightOn(light)

def allOff():
  for light in range(1,13):
    lightOff(light)

def updateMainLed():
    global lightsOff
    GPIO.output(GREEN_LED_PIN, not lightsOff)

def blinkAll(times, sleepTime):
    global blinking
    def changeButtonStates(on):
        GPIO.output(BLUE_LED_PIN, on)
        GPIO.output(RED_LED_PIN, on)
        GPIO.output(SQUARE_LED_PIN, on)
        
    def allOn():
        changeButtonStates(True)

    def allOff():
        changeButtonStates(False)

    def blink():
        allOn()
        time.sleep(sleepTime)
        allOff()
        time.sleep(sleepTime)

    blinking = True
    for i in range(0,times):
        blink()
    blinking = False

def circleBlink(circleTimes, sleepTime):
    global blinking
    def circleOnce():
        GPIO.output(BLUE_LED_PIN, True)
        time.sleep(sleepTime)
        GPIO.output(BLUE_LED_PIN, False)
        time.sleep(sleepTime)
        GPIO.output(RED_LED_PIN, True)
        time.sleep(sleepTime)
        GPIO.output(RED_LED_PIN, False)
        time.sleep(sleepTime)
        GPIO.output(SQUARE_LED_PIN, True)
        time.sleep(sleepTime)
        GPIO.output(SQUARE_LED_PIN, False)
        time.sleep(sleepTime)

    blinking = True
    for i in range(0,circleTimes):
        circleOnce()
    blinking = False

def blinkAllThreeTimes():
    blinkAll(3, SLOW_BLINK_TIME)

def blinkAllSixTimes():
    blinkAll(10, FAST_BLINK_TIME)

def indicateSave():
    blinkAllThreeTimes()

def indicateClear():
    blinkAllSixTimes()

def indicateClearAll():
    circleBlink(10, REALLY_FAST_BLINK_TIME)

def indicateSwitch():
    blinkAll(2, FAST_BLINK_TIME)

def toggleLights():
    global lightsOff
    if lightsOff:
        allOn()
    else:
        allOff()

def ReadChannel(channel):
    global spi
    adc = spi.xfer2([1, (8+channel)<<4, 0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

def ConvertToBrightness(data):
    # 255 range
    brightness = (1024 - data) / 4 
    return brightness


def readKnob():
    reading = ReadChannel(KNOB_CHANNEL)
    return ConvertToBrightness(reading)

def changeBrightness(lightnum, brightness):
  url = makeStateUrl(lightnum)
  data = "{\"bri\": %d}" % brightness
  if (lightnum == 10):
      print("  Brightness: %d"%brightness)
  put(url, data)


def updateBrightness():
    jsonText = get(BASE_URL)
    lightsJson = json.loads(jsonText)
    for light, info in lightsJson.iteritems():
        lightCurve = lightToCurve[light]
        brightness = computeBrightness(lastKnob, lightCurve)
        changeBrightness(int(light), brightness)


def knobCheckWorker():
    global lastKnob

    # Take a first reading, so we can detect the first move
    lastKnob = readKnob()
    while True:
        knob = readKnob()
        # We want some threshold to prevent jitter
        if (abs(knob - lastKnob) > JITTER_TOLERANCE):
            # flatten extremes
            if (knob <= JITTER_TOLERANCE):
                knob = 0
            elif (knob >= KNOB_MAX - JITTER_TOLERANCE):
                knob = KNOB_MAX
            lastKnob = knob
            print("Knob:%d" % lastKnob)
            updateBrightness()
    time.sleep(CHECK_KNOB_SLEEP_TIME)

def sceneIsDifferent(scene1, scene2):
    return False

def updateScene(scene):
    print("Updating Scene")

def readScene(json):
    pass


def lightCheckWorker():
    global lightsOff
    global currentScene
    while True:
        time.sleep(CHECK_LIGHTS_SLEEP_TIME)
        # Fetch json
        jsonText = get(BASE_URL)
        lightsJson = json.loads(jsonText)

        # If lights have changed (e.g., by phone), update light state
        newLightsOff = allLightsAreOff(lightsJson)        
        if newLightsOff != lightsOff:
            lightsOff = newLightsOff
            updateMainLed()
        lightsOff = newLightsOff

        # Grab the current scene.  If it's different from the old one, update curves etc
        newScene = readScene(lightsJson)
        if sceneIsDifferent(newScene, currentScene):
            updateScene(newScene)
        currentScene = newScene

def saveLights():
    print("Saving lights")

def clearLights():
    print("Clearing lights")

def clearAllLights():
    print("Clearing all lights")

def switchLightsBackward():
    print("Switching lights backward")

def switchLightsForward():
    print("Switching lights forward")


# Blue button
def blueLongPressAction():
    threading.Thread(target=saveLights).start()
    indicateSave()

def blueShortPressAction():
    threading.Thread(target=switchLightsForward).start()
    indicateSwitch()
    
def blueButtonCheckWorker():
    buttonCheckWorker(BLUE_BUTTON_PIN, BLUE_LED_PIN, blueShortPressAction, blueLongPressAction)

# Red button
def redLongPressAction():
    threading.Thread(target=clearLights).start()
    indicateClear()

def redShortPressAction():
    threading.Thread(target=switchLightsBackward).start()
    indicateSwitch()

def redButtonCheckWorker():
    buttonCheckWorker(RED_BUTTON_PIN, RED_LED_PIN, redShortPressAction, redLongPressAction)

# Square button
def squareLongPressAction():
    threading.Thread(target=clearAllLights).start()
    indicateClearAll()

def squareShortPressAction():
    threading.Thread(target=toggleLights).start()
    indicateSwitch()

def squareButtonCheckWorker():
    buttonCheckWorker(SQUARE_BUTTON_PIN, SQUARE_LED_PIN, squareShortPressAction, squareLongPressAction)


# Detects short or long press.  Does action depending on short/long.   Configurable for different buttons/lights.
def buttonCheckWorker(buttonPin, buttonLightPin, shortPressAction, longPressAction):
    global blinking

    def updateLed(isOn):
        if blinking:
            return
        GPIO.output(buttonLightPin, isOn)

    while True:
        detectedPress = False
        detectedLongPress = False
        updateLed(False)
        time.sleep(CHECK_BUTTON_SLEEP_TIME)
        # Button is normally high.  If it's low, it's been pressed
        input_value = GPIO.input(buttonPin)
        start = 0
        if input_value == False:
            detectedPress = True
            updateLed(True)
            # Start a timer, when the timer is exceeded, we've detected a long press
            start = time.time()
	while input_value == False and not detectedLongPress:
            time.sleep(CHECK_BUTTON_SLEEP_TIME)
            input_value = GPIO.input(buttonPin)
            timeHeld = time.time() - start
            if (timeHeld > LONG_PRESS_TIME):
                updateLed(False)
                detectedLongPress = True
                longPressAction()
                # wait until the button is released, so the main loop starts fresh
                while input_value == False:
                    time.sleep(CHECK_BUTTON_SLEEP_TIME)
                    input_value = GPIO.input(buttonPin)
        if detectedPress and not detectedLongPress:
            shortPressAction()



def init():
    global lightsOff
    global spi
    spi = spidev.SpiDev()
    spi.open(0,0)
    jsonText = get(BASE_URL)
    lightsJson = json.loads(jsonText)
    lightsOff = allLightsAreOff(lightsJson)
    computeBrightnessCurves()
    updateMainLed()

def startWorkerThreads():
    threading.Thread(target=lightCheckWorker).start()
    threading.Thread(target=blueButtonCheckWorker).start()
    threading.Thread(target=redButtonCheckWorker).start()
    threading.Thread(target=squareButtonCheckWorker).start()
    threading.Thread(target=knobCheckWorker).start()

init()
startWorkerThreads()


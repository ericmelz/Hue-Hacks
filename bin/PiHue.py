#!/usr/bin/python

# This is code for a Hue Light controller.
# It consists of 3 buttons and a knob.
#
# The 3 buttons are:
# - a large square LED which serves as the main button
# - a red button which is the "back" button
# - a blue button which is the "forward" button
#
# The primary functions of the button are triggered with a "short press"
# These are:
# - Square button: toggle lights on or off
# - Red Button: Switch to the previous scene
# - Blue Button: Switch to the next scene
#
# A long press will trigger a secondary functinon.  The secondary functions are:
# - Square button: clear all scenes
# - Red Button: Delete the current scene
# - Blue Button: Save the current scene
#
# Additionally, a knob is used to dim the lights.
#
# An led is used to indicate that the lights are in the "on" state.
# 
# There are a few led-blinking patterns that have meaning.
# They are as follows:
# - blinkAllThreeTimes - indicates save
# - blinkAllSixTimes - indicates clear
# - circleBlink - indicates clear all
# - blinkTwice - indicates switching scenes
#
# Log data is saved at /var/piHue/logs

# TODO log.debug events like switching scenes

from __future__ import division
import RPi.GPIO as GPIO
import json
import logging
import logging.handlers
import os
import pickle
import spidev
import threading
import time
import urllib2
import ConfigParser

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

CHECK_LIGHTS_SLEEP_TIME = 0.5
CHECK_BUTTON_SLEEP_TIME = 0.05
CHECK_KNOB_SLEEP_TIME = .05

SLOW_BLINK_TIME = .4
FAST_BLINK_TIME = .1
REALLY_FAST_BLINK_TIME = .05

LONG_PRESS_TIME = 2.0

DISCOVERY_URL = "https://www.meethue.com/api/nupnp"
DATA_DIR = "/var/piHue"
LOGS_DIR = "/var/piHue/logs"
LOG_FILE_BASE = "/var/piHue/logs/pieHue.log"
DATA_FILE = "/var/piHue/scenes.p"
CONFIG_FILE = "%s/piHue.conf" % DATA_DIR
HUE_SECTION = "Hue"
BRIDGE_IP_OPTION = "bridgeIp"


# Address of Hue Bridge
bridgeIp = None

# Indicates whether Hue lights are off.
lightsOff = True

# If true, then we let the blink routine override other LED updates
blinking = False

# Saved brightness
lastKnob = 0

# Map from light IDs to curves
lightToCurve = {}

# Index of current scene
currentScene = 0

# Representation of current scene
currentSceneObj = None

class Scene:
    def __init__(self):
        self.lights = {}

    def addLight(self, lightnum, light):
        self.lights[lightnum] = light

    def __str__(self):
        s = "[\n"
        for k in sorted(self.lights.keys()):
            v = self.lights[k]
            s += "  " + str(k) + " -> " + str(v) + "\n"
        return s + "]"
            
class Light:
    def __init__(self, name, lightState):
        self.name = name
        self.lightState = lightState

    def __str__(self):
        return "[light: name=%s, state=%s]" % (self.name, self.lightState)

class LightState:
    def __init__(self, bri, mode, ct, xy, on):
        self.bri = bri
        self.mode = mode
        self.ct = ct
        self.xy = xy
        self.on = on

    def __str__(self):
        return "[lightState: bri=%s, mode=%s, ct=%s, xy=%s on=%s]" % (self.bri, self.mode, self.ct, self.xy, self.on)

scenes = []

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


def getBaseUrl():
    baseUrl = "http://%s/api/newdeveloper/lights" % bridgeIp
    return baseUrl

def makeStateUrl(lightnum):
    return "%s/%d/state" % (getBaseUrl(), lightnum)

def updateCt(lightnum, ct):
  url = makeStateUrl(lightnum)
  data = "{\"ct\": %d}" % ct
  put(url, data)

def updateBri(lightnum, bri):
  url = makeStateUrl(lightnum)
  data = "{\"bri\": %d}" % bri
  put(url, data)

def updateColormode(lightnum, colormode):
  url = makeStateUrl(lightnum)
  data = "{\"colormode\": %s}" % colormode
  put(url, data)

def updateXy(lightnum, xy):
  url = makeStateUrl(lightnum)
  data = "{\"xy\": [%s, %s]}" % xy
  put(url, data)

def updateOn(lightnum, isOn):
  url = makeStateUrl(lightnum)
  data = "{\"on\": %s}" % str(isOn).lower()
  put(url, data)

def updateLight(lightnum, light):
    state = light.lightState
    updateColormode(lightnum, state.mode)
    updateCt(lightnum, state.ct)
    updateXy(lightnum, state.xy)
    updateBri(lightnum, state.bri)
    updateOn(lightnum, state.on)

def updateScene(scene):
    global currentSceneObj
    currentSceneObj = scene
    for lightnum, light in scene.lights.iteritems():
        updateLight(int(lightnum), light)

def fetchHueBridgeIp():
    jsonText = get(DISCOVERY_URL)
    bridgesJson = json.loads(jsonText)
    bridgeJson = bridgesJson[0] # grab the first bridge
    logger.info("bridgeJson is %s" % str(bridgeJson))
    return bridgeJson['internalipaddress']

def writeConfig(bridgeIp):
    f = open(CONFIG_FILE, 'w')
    f.write("[%s]\n%s=%s" % (HUE_SECTION, BRIDGE_IP_OPTION, bridgeIp))
    f.close

def printState():
  lightsJson = get(getBaseUrl())
  print(str(lightsJson))

def saveScene():
    logger.info("saving scene")
    # TODO this logic can be refactored into readScene, used during lightCheckworker
    jsonText = get(getBaseUrl())
    lightsJson = json.loads(jsonText)
    scene = Scene()
    scenes.insert(currentScene, scene)
    for lightnum, info in lightsJson.iteritems():
        name = info['name']
        state = info['state']
        bri = state['bri']
        mode = state['colormode']
        ct = state['ct']
        on = state['on']
        xyArray = state['xy']
        xyTuple = (xyArray[0], xyArray[1])
        lightState = LightState(bri,mode,ct,xyTuple,on)
        light = Light(name, lightState)
        scene.addLight(lightnum, light)
    saveData()

def deleteScene():
    global scenes
    logger.info("deleting scene")
    if (len(scenes) > 0):
        scene = scenes[currentScene]
        scenes.remove(scene)
        saveData()
    # Try to make currentScene in an ok state.  If there's no scenes left, nothing happens
    previousScene()
        

def nextScene():
    global currentScene
    if len(scenes) > 0:
        logger.info("moving to next scene")
        currentScene = (currentScene + 1) % len(scenes)
        updateScene(scenes[currentScene])

def previousScene():
    global currentScene
    if (len(scenes) > 0):
        logger.info("moving to previous scene")
        currentScene = currentScene - 1
        if (currentScene < 0):
            currentScene = len(scenes) - 1
        updateScene(scenes[currentScene])

def dumpInfo():
    logger.info("There are %d scenes saved." % len(scenes))
    logger.info("Current scene: %d" % currentScene)
    logger.info("Scenes:")
    for i in range(0,len(scenes)):
        logger.info(str(scenes[i]))

def loadData():
    global scenes
    scenes = pickle.load(open(DATA_FILE, "rb"))

def saveData():
    pickle.dump(scenes, open(DATA_FILE, "wb"))

def readConfig():
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIG_FILE))
    bridgeIp = config.get(HUE_SECTION, BRIDGE_IP_OPTION)
    return bridgeIp

def ensureDir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

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
    jsonText = get(getBaseUrl())
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
    logger.info("Toggling lights")
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
  put(url, data)


def updateBrightness():
    jsonText = get(getBaseUrl())
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
        try:
            knob = readKnob()
            # We want some threshold to prevent jitter
            if (abs(knob - lastKnob) > JITTER_TOLERANCE):
                # flatten extremes
                if (knob <= JITTER_TOLERANCE):
                    knob = 0
                elif (knob >= KNOB_MAX - JITTER_TOLERANCE):
                    knob = KNOB_MAX
                lastKnob = knob
                updateBrightness()
            time.sleep(CHECK_KNOB_SLEEP_TIME)
        except Exception as ex:
            logger.exception(ex)



# TODO what's this for?  finish it
def sceneIsDifferent(scene1, scene2):
    return False

# TODO what's this for?  finish it
def readScene(json):
    pass

def lightCheckWorker():
    global lightsOff
    global currentSceneObj
    while True:
        try:
            time.sleep(CHECK_LIGHTS_SLEEP_TIME)
            # Fetch json
            jsonText = get(getBaseUrl())
            lightsJson = json.loads(jsonText)

            # If lights have changed (e.g., by phone), update light state
            newLightsOff = allLightsAreOff(lightsJson)        
            if newLightsOff != lightsOff:
                lightsOff = newLightsOff
                updateMainLed()
                lightsOff = newLightsOff

            # TODO impleme this logic...
            # Grab the current scene.  If it's different from the old one, update curves etc
            newSceneObj = readScene(lightsJson)
            if sceneIsDifferent(newSceneObj, currentSceneObj):
                updateScene(newSceneObj)
                currentSceneObj = newSceneObj

        except Exception as ex:
            logger.exception(ex)

def saveLights():
    try:
        logger.info("Saving lights")
        saveScene()
    except Exception as ex:
        logger.exception(ex)


def clearLights():
    try:
        logger.info("Clearing lights")
        deleteScene()
    except Exception as ex:
        logger.exception(ex)

def clearAllLights():
    try:
        # TODO implement this
        logger.info("Clearing all lights")
    except Exception as ex:
        logger.exception(ex)

def switchLightsBackward():
    try:
        logger.info("Switching lights backward")
        previousScene()
    except Exception as ex:
        logger.exception(ex)

def switchLightsForward():
    try:
        logger.info("Switching lights forward")
        nextScene()
    except Exception as ex:
        logger.exception(ex)

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
#    threading.Thread(target=clearAllLights).start()
    threading.Thread(target=dumpInfo).start()
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
        try:
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
        except Exception as ex:
            logger.exception(ex)

def initADC():
    global spi
    spi = spidev.SpiDev()
    spi.open(0,0)


def initLightState():
    global lightsOff
    jsonText = get(getBaseUrl())
    lightsJson = json.loads(jsonText)
    lightsOff = allLightsAreOff(lightsJson)

def initLogger():
    global logger

    ensureDir(LOGS_DIR)

    logger = logging.getLogger('logjam')
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(LOG_FILE_BASE, maxBytes=1000000, backupCount=20)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def initConfig():
    global bridgeIp

    ensureDir(DATA_DIR)
    if not os.path.exists(CONFIG_FILE):
        logger.info("config file doesn't exist.  Going to create.")
        logger.info("Fetching bridge ip...")
        ip = fetchHueBridgeIp()
        logger.info("Writing config..")
        writeConfig(ip)
        logger.info("Reading config...")
        bridgeIp = readConfig()
    logger.info("Reading config...")
    bridgeIp = readConfig()


def loadScenes():
    try:
        logger.info("Attempting to load the scene file..")
        loadData()
        logger.info("Successfully loaded scenes.")
    except:
        logger.warn("Load not successful.  Could be first launch or the data file may have been deleted or corrupted.")


def init():
    try:
        initLogger()
        logger.info("Initializing system.")
        initConfig()
        initADC()
        initLightState()
        logger.info("Bridge ip is %s" % bridgeIp)
        computeBrightnessCurves()
        updateMainLed()
        loadScenes()
    except Exception as ex:
        print("ex is %s" % str(ex))
        logger.exception(ex)

def startWorkerThreads():
    threading.Thread(target=lightCheckWorker).start()
    threading.Thread(target=blueButtonCheckWorker).start()
    threading.Thread(target=redButtonCheckWorker).start()
    threading.Thread(target=squareButtonCheckWorker).start()
    threading.Thread(target=knobCheckWorker).start()

init()
startWorkerThreads()



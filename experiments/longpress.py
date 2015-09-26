#!/usr/bin/python

# A simple script to detect long and short presses

import RPi.GPIO as GPIO
import threading
import time

BLUE_LED_PIN = 13
RED_LED_PIN = 15
SQUARE_LED_PIN = 18
RED_BUTTON_PIN = 8
BLUE_BUTTON_PIN = 10
SQUARE_BUTTON_PIN = 16

SLOW_BLINK_TIME = .4
FAST_BLINK_TIME = .1
REALLY_FAST_BLINK_TIME = .05

LONG_PRESS_TIME = 2.0

CHECK_BUTTON_SLEEP_TIME = 0.05

GPIO.setmode(GPIO.BOARD)
GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(SQUARE_LED_PIN, GPIO.OUT)
GPIO.setup(BLUE_BUTTON_PIN, GPIO.IN)
GPIO.setup(RED_BUTTON_PIN, GPIO.IN)
GPIO.setup(SQUARE_BUTTON_PIN, GPIO.IN)

# If true, then we let the blink routine override other LED updates
blinking = False

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

def updateBlueLed(isOn):
    GPIO.output(BLUE_LED_PIN, isOn)

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

def toggleLights():
    print("Toggling lights")

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


def startWorkerThreads():
    threading.Thread(target=blueButtonCheckWorker).start()
    threading.Thread(target=redButtonCheckWorker).start()
    threading.Thread(target=squareButtonCheckWorker).start()

startWorkerThreads()

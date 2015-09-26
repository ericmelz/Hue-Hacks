#!/usr/bin/python

# A simple script to blink an LED light 

import RPi.GPIO as GPIO
import threading
import time

# blue is 13, red is 15, square is 19
#ledPin = 13
#ledPin = 15
ledPin = 19
sleepTime = .5

GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledPin, GPIO.OUT)

def updateLED():
    global ledOn
    GPIO.output(ledPin, ledOn)

def init():
    global ledOn 
    ledOn = False
    updateLED()

def lightBlinkWorker():
    global ledOn
    while True:
        time.sleep(sleepTime)
        ledOn = not ledOn
        updateLED()


def startWorkerThreads():
    lightBlinkerThread = threading.Thread(target=lightBlinkWorker)
    lightBlinkerThread.start()

init()
startWorkerThreads()


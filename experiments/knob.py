#!/usr/bin/python

import spidev
import threading
import time


knobChannel = 0
lastBrightness = 0
jitterTolerance = 8
checkKnobSleeptime = .05

# Open SPI bus
def init():
    global spi
    spi = spidev.SpiDev()
    spi.open(0,0)

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
    global spi
    adc = spi.xfer2([1, (8+channel)<<4, 0])
    data = ((adc[1]&3) << 8) + adc[2]
#    print("data=%d"%data)
    return data

def ConvertToBrightness(data):
    brightness = (1024 - data) / 4
    return brightness


def readBrightness():
    reading = ReadChannel(knobChannel)
    return ConvertToBrightness(reading)

def knobCheckWorker():
    global lastBrightness

    # Take a first reading, so we can detect the first move
    lastBrightness = readBrightness()
    while True:
        brightness = readBrightness()
        # We want some threshold to prevent jitter
        if (abs(brightness - lastBrightness) > jitterTolerance):
            # flatten extremes
            if (brightness < jitterTolerance):
                brightness = 0
            elif (brightness > 256 - jitterTolerance):
                brightness = 256
            lastBrightness = brightness
            print("Brightness: %d" % lastBrightness)
    time.sleep(checkKnobSleeptime)
    

def startWorkerThreads():
    knobCheckerThread = threading.Thread(target=knobCheckWorker)
    knobCheckerThread.start()

init()
startWorkerThreads()

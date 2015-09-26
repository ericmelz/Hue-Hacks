#!/usr/bin/python

# A simple script to toggle an LED light using a pushbutton

import RPi.GPIO as GPIO
import urllib2

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(12, GPIO.IN)

def put(url, data):
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url, data=data)
    request.get_method = lambda: 'PUT'
    result = opener.open(request)

def makeStateUrl(lightnum):
    return "http://192.168.1.62/api/newdeveloper/lights/%d/state" % lightnum

def lightOn(light):
    url = makeStateUrl(light)
    data = "{\"on\": true}"
    put(url, data)

def lightOff(light):
    url = makeStateUrl(light)
    data = "{\"on\": false}"
    put(url, data)


light = False
while True:
    input_value = GPIO.input(12)
    if input_value == False:
        light = not light
        GPIO.output(11, light)
        if light:
            lightOn(10)
        else:
            lightOff(10)
	while input_value == False:
            input_value = GPIO.input(12)


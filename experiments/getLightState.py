#!/usr/bin/python

# A simple script to detect the on-off state of the lights

import urllib2
import json
import time
import threading

sleeptime = 0.5

def get(url):
    response = urllib2.urlopen(url)
    result = response.read()
    return result

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print '%s function took %0.3f ms' % (f.func_name, (time2-time1) * 1000.0)
        return ret
    return wrap

@timing
def allLightsAreOff():
    jsonText = get('http://192.168.1.62/api/newdeveloper/lights')
    lightsJson = json.loads(jsonText)
    for name, info in lightsJson.iteritems():
        state = info['state']
        on = state['on']
        if on:
            return False
    return True

def lightCheckWorker():
    """light worker function"""
    previousState = allLightsAreOff()
    while True:
        time.sleep(sleeptime)
        currentState = allLightsAreOff()        
        if currentState != previousState:
            state = 'Off' if currentState else 'On'
            print("lights are now %s" % state)
        previousState = currentState
        
#for i in range(1,20):
#    print("allLightsAreOff=" + str(allLightsAreOff()))
#    allLightsAreOff()

checkerThread = threading.Thread(target=lightCheckWorker)
checkerThread.start()


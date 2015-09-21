#!/usr/bin/python

import urllib2
import json
import pprint

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
    def __init__(self, bri, mode, ct, on):
        self.bri = bri
        self.mode = mode
        self.ct = ct
        self.on = on

    def __str__(self):
        return "[lightState: bri=%s, mode=%s, ct=%s, on=%s]" % (self.bri, self.mode, self.ct, self.on)

scenes = []

def get(url):
  response = urllib2.urlopen(url)
  return response.read()

def makeStateUrl(lightnum):
  return "http://192.168.1.62/api/newdeveloper/lights/%d/state" % lightnum

BASE_URL = "http://192.168.1.62/api/newdeveloper/lights"

def printState():
  lightsJson = get(BASE_URL)
  print(str(lightsJson))

def saveScene():
    print("saving scene")
    jsonText = get(BASE_URL)
    lightsJson = json.loads(jsonText)
    scene = Scene()
    scenes.append(scene)
    for lightnum, info in lightsJson.iteritems():
        name = info['name']
        state = info['state']
        bri = state['bri']
        mode = state['colormode']
        ct = state['ct']
        on = state['on']
        lightState = LightState(bri,mode,ct,on)
        light = Light(name, lightState)
        scene.addLight(lightnum, light)

def deleteScene():
    print("deleting scene")

def nextScene():
    print("moving to next scene")

def previousScene():
    print("moving to previous scene")

def dumpInfo():
    print("There are %d scenes saved." % len(scenes))
    print("Scenes:")
    for i in range(0,len(scenes)):
        print(str(scenes[i]))

def printHelp():
    print("Commands:")
    print("  [s]ave scene")
    print("  [d]elete scene")
    print("  [n]ext scene")
    print("  [p]revious scene")
    print("  [i]info")
    print("  [q]uit")
    print("  [?] help")


while True:
    input = raw_input("Enter command: [s,d,n,p,i,?,q]):")
    if (input == 's'):
        saveScene()
    elif (input == 'd'):
        deleteScene()
    elif (input == 'n'):
        nextScene()
    elif (input == 'p'):
        previousScene()
    elif (input == 'i'):
        dumpInfo()
    elif (input == '?'):
        printHelp()
    elif (input == 'q'):
        break
    else:
        print("I'm sorry eric, I'm afraid I can't help you.")
    
    
    
    
          

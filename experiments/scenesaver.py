#!/usr/bin/python

import urllib2
import json
import pprint

BASE_URL = "http://192.168.1.62/api/newdeveloper/lights"

currentScene = 0

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

def makeStateUrl(lightnum):
  return "%s/%d/state" % (BASE_URL, lightnum)

def get(url):
  response = urllib2.urlopen(url)
  return response.read()

def put(url, data):
  opener = urllib2.build_opener(urllib2.HTTPHandler)
  request = urllib2.Request(url, data=data)
  request.get_method = lambda: 'PUT'
  result = opener.open(request)

def makeStateUrl(lightnum):
  return "http://192.168.1.62/api/newdeveloper/lights/%d/state" % lightnum

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
    for lightnum, light in scene.lights.iteritems():
        updateLight(int(lightnum), light)

def printState():
  lightsJson = get(BASE_URL)
  print(str(lightsJson))

def saveScene():
    print("saving scene")
    jsonText = get(BASE_URL)
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

def deleteScene():
    print("deleting scene")

def nextScene():
    global currentScene
    print("moving to next scene")
    currentScene = (currentScene + 1) % len(scenes)
    updateScene(scenes[currentScene])

def previousScene():
    print("moving to previous scene")

def dumpInfo():
    print("There are %d scenes saved." % len(scenes))
    print("Current scene: %d" % currentScene)
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
    
    
    
    
          

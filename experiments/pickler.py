#!/usr/bin/python

# Note: you must run this as root in order for access to /var to work

import pickle

DATA_FILE = "/var/piHue/scenes.p"

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

def printData():
    print("Scenes:")
    for i in range(0,len(scenes)):
        print(str(scenes[i]))

def makeData():
    # Scene 1
    scene = Scene()
    scenes.append(scene)
    name = 'light1'
    lightnum = '1'
    bri = 1
    mode = 'xy'
    ct = 300
    xyTuple = (1,2)
    on = True
    lightState = LightState(bri,mode,ct,xyTuple,on)
    light = Light(name, lightState)
    scene.addLight(lightnum, light)

    name = 'light2'
    lightnum = '2'
    bri = 22
    mode = 'ct'
    ct = 300
    xyTuple = (2,3)
    on = True
    lightState = LightState(bri,mode,ct,xyTuple,on)
    light = Light(name, lightState)
    scene.addLight(lightnum, light)

    # Scene 2
    scene = Scene()
    scenes.append(scene)
    name = 'light3'
    lightnum = '3'
    bri = 11
    mode = 'xy'
    ct = 330
    xyTuple = (3,4)
    on = True
    lightState = LightState(bri,mode,ct,xyTuple,on)
    light = Light(name, lightState)
    scene.addLight(lightnum, light)

    name = 'light4'
    lightnum = '4'
    bri = 44
    mode = 'ct'
    ct = 345
    xyTuple = (4,5)
    on = False
    lightState = LightState(bri,mode,ct,xyTuple,on)
    light = Light(name, lightState)
    scene.addLight(lightnum, light)

def loadData():
    global scenes
    scenes = pickle.load(open(DATA_FILE, "rb"))

def saveData():
    pickle.dump(scenes, open(DATA_FILE, "wb"))

def init():
    # try loading a file
    print("Attempting to load a file")
    
    try:
        loadData()
        print("Successfully loaded.")
        printData()
    except:
        print("Load not successful.  Creating some test data")
        makeData()
        saveData()
        print("Saved the data")
        
    
init()

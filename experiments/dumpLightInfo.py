#!/usr/bin/python

# Usage: ./dumpLightInfo.py | python -m json.tool

import urllib2
import json

def get(url):
  response = urllib2.urlopen(url)
  return response.read()

def makeStateUrl(lightnum):
  return "http://192.168.1.62/api/newdeveloper/lights/%d/state" % lightnum

def printState():
#  lightJson = get(makeStateUrl(2))
  lightsJson = get("http://192.168.1.62/api/newdeveloper/lights")
  print(str(lightsJson))
  
printState()

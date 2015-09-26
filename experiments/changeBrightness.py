#!/usr/bin/python

import urllib2

def put(url, data):
  opener = urllib2.build_opener(urllib2.HTTPHandler)
  request = urllib2.Request(url, data=data)
  request.get_method = lambda: 'PUT'
  result = opener.open(request)

def makeStateUrl(lightnum):
  return "http://192.168.1.62/api/newdeveloper/lights/%d/state" % lightnum

def changeBrigthness(lightnum, bri):
  url = makeStateUrl(lightnum)
  data = "{\"bri\": %d}" % bri
  put(url, data)

changeBrigthness(10, 0)

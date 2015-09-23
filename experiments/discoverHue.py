#!/usr/bin/python

import urllib2
import json
import logging
import logging.handlers
import ConfigParser
import os


DISCOVERY_URL = "https://www.meethue.com/api/nupnp"
DATA_DIR = "/var/piHue"
LOGS_DIR = "/var/piHue/logs"
LOG_FILE_BASE = "/var/piHue/logs/pieHue.log"
CONFIG_FILE = "%s/piHue.conf" % DATA_DIR
HUE_SECTION = "Hue"
BRIDGE_IP_OPTION = "bridgeIp"

bridgeIp = None

def get(url):
    response = urllib2.urlopen(url)
    result = response.read()
    return result

def fetchHueBridgeIp():
    jsonText = get(DISCOVERY_URL)
    bridgesJson = json.loads(jsonText)
    bridgeJson = bridgesJson[0] # grab the first bridge
    return bridgeJson['internalipaddress']

def writeConfig(bridgeIp):
    f = open(CONFIG_FILE, 'w')
    f.write("[%s]\n%s=%s" % (HUE_SECTION, BRIDGE_IP_OPTION, bridgeIp))
    f.close

def readConfig():
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIG_FILE))
    bridgeIp = config.get(HUE_SECTION, BRIDGE_IP_OPTION)
    return bridgeIp

def ensureDir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def initLogger():
    global logger

    ensureDir(LOGS_DIR)

    logger = logging.getLogger('logjam')
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler(LOG_FILE_BASE, maxBytes=1000000, backupCount=3)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def initConfig():
    global bridgeIp
    ensureDir(DATA_DIR)
    if not os.path.exists(CONFIG_FILE):
        logger.info("config file doesn't exist.  Going to create.")
        logger.info("Fetching bridge ip...")
        ip = fetchHueBridgeIp()
        logger.info("Writing config..")
        writeConfig(ip)
    logger.info("Reading config...")
    bridgeIp = readConfig()

def init():
    try:
        initLogger()
        logger.info("Starting...")
        initConfig()
    except Exception as ex:
        logger.exception(ex)

init()
logger.info("bridge ip is %s" % bridgeIp)

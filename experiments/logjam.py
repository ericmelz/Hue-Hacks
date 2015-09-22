#!/usr/bin/python

import logging
import logging.handlers

def init():
    global logger
    logger = logging.getLogger('logjam')
    logger.setLevel(logging.DEBUG)

    handler = logging.handlers.RotatingFileHandler('logjam.log', maxBytes=1000000, backupCount=3)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
def doSomething():
    global logger
    try:
        logger.warning("Hey, I'm doing something!")
        raise Exception('yowza')
    except Exception as ex:
        logger.exception(ex)
        
        

init()
for i in range(2):
    doSomething()

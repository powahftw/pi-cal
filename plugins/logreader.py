from .plugin import Plugin
import logging
import json 

logging = logging.getLogger(__name__)
CONFIG = json.load(open("config.json"))

class LogReader(Plugin):

    name = "LOG READER"
    LOG_FILE_PATH = CONFIG["LOG_PATH"]

    def __init__(self, position):
        Plugin.__init__(self, position)

    def update(self):
        with open(LogReader.LOG_FILE_PATH, 'r') as f:
            return f.read().splitlines()[-1]

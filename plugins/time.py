from .plugin import Plugin
import logging
from datetime import datetime


logging = logging.getLogger(__name__)

class Time(Plugin):
    
    name = "TIME"

    def __init__(self, position):
        Plugin.__init__(self, position)
    
    def update(self):
        now = datetime.now()
        time = f"{now.hour}:{now.minute:02}"
        logging.info(f"Current time is {time}")
        return [time], None

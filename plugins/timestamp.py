from .plugin import Plugin
import logging
from datetime import datetime


logging = logging.getLogger(__name__)

class Timestamp(Plugin):
    
    name = "TIMESTAMP"
    INCLUDE_TIME = True

    def __init__(self, position):
        Plugin.__init__(self, position)
    
    def update(self):
        current_date = datetime.today().strftime("%Y-%m-%d") 
        if self.INCLUDE_TIME:
            now = datetime.now()
            time = f"{now.hour}:{now.minute:02}"
            current_date += f" {time}"
        return [current_date], None

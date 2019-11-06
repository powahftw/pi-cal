from .plugin import Plugin
import logging
from datetime import datetime


logging = logging.getLogger(__name__)

class Timestamp(Plugin):
    
    name = "TIMESTAMP"

    def __init__(self, position):
        Plugin.__init__(self, position)
    
    def update(self):
        current_date = datetime.today().strftime("%Y-%m-%d") 
        logging.info(f"Current date is {current_date}")
        return [current_date], None

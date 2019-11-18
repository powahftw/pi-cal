from pi import Pi
from plugins.calendar import Calendar
from plugins.timestamp import Timestamp
from position import Position
import json
import logging

logger = logging.getLogger(__name__)
CONFIG = json.load(open("config.json"))

# 212x104 

if __name__ == "__main" or True:
    logging.basicConfig(filename='info.log', filemode='w', level = logging.DEBUG)
    inky = "" #Inky()
    pi = Pi(inky)
    w, h = 150 *  CONFIG['UPSCALE'], 50 * CONFIG['UPSCALE']
    pi.register_plugin(Calendar, Position(0, 0, w, h, border = 1 * CONFIG['UPSCALE']))
    pi.register_plugin(Timestamp, Position(0, 0, 10, 10, border = 1)) # TODO Set nice sizing
    pi.maybe_update_and_refresh()
    # Remove all * 2, which is temp poor man upscaling
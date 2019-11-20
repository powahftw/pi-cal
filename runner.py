from inky import InkyPHAT
from pi import Pi
from plugins.calendar import Calendar
from plugins.timestamp import Timestamp
from position import Position
import json
import logging

logger = logging.getLogger(__name__)
CONFIG = json.load(open("config.json"))

# 212x104 

if __name__ == "__main__":
    logging.basicConfig(filename='info.log', filemode='w', level = logging.DEBUG)
    inky =  InkyPHAT('black')
    pi = Pi(inky)
    
    w, h, border = 150 *  CONFIG['UPSCALE'], 50 * CONFIG['UPSCALE'], 1 * CONFIG['UPSCALE']
    TOP_LEFT = Position(0, 0, w, h, border)
    BOTTOM_RIGHT = Position(inky.WIDTH * CONFIG['UPSCALE'] - 140, inky.WIDTH * CONFIG['UPSCALE'] - 45, 140, 45, border)

    pi.register_plugin(Calendar, TOP_LEFT)
    pi.register_plugin(Timestamp, BOTTOM_RIGHT)
    pi.maybe_update_and_refresh()
    # Remove all * 2, which is temp poor man upscaling
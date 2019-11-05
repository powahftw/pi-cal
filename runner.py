from pi import Pi
from plugins.calendar import Calendar
from position import Position
import json
import logging

logger = logging.getLogger(__name__)
CONFIG = json.load(open("config.json"))

if __name__ == "__main" or True:
    logging.basicConfig(filename='info.log', filemode='w', level = logging.DEBUG)
    inky = "" #Inky()
    pi = Pi(inky)
    w, h = 150 * 2, 50 * 2
    pi.register_plugin(Calendar, Position(0, 0, w, h, border = 1 * 2))
    pi.maybe_update_and_refresh()
    # Remove all * 2
from pi import Pi
from plugins.calendar import Calendar
from plugins.timestamp import Timestamp
from plugins.time import Time
from plugins.memused import MemUsed
from plugins.logreader import LogReader
from position import Position
import json
import uuid
import logging
import time

logger = logging.getLogger(__name__)
CONFIG = json.load(open("config.json"))

RUNNING_ON_PI = False
if RUNNING_ON_PI:
    from inky import InkyPHAT
else:
    # Inky library works nicely only on the pi.
    # For testing locally we use a Mock which mimick the Inky class but save to img/ instead of displaying it them.
    class InkyMock():
        WIDTH, HEIGHT = 212, 104
        WHITE, BLACK = 0, 1
        def __init__(self):
            self.times = 0

        def set_image(self, screen):
            self.screen = screen

        def show(self):
            filename = f"img/{self.times}-{uuid.uuid4().hex}.png"
            if self.screen:
                self.screen.save(filename)
                self.times += 1

# 212x104 

if __name__ == "__main__":
    logging.basicConfig(filename='info.log', filemode='w', level = logging.DEBUG)
    inky = InkyPHAT('black') if RUNNING_ON_PI else InkyMock()
    pi = Pi(inky)
    # 10 x 6 GRID
    upscale = CONFIG["UPSCALE"]
    TOP_HALF = Position.grid_to_pixels("FIRST_10", "FIRST_3", border = 1, upscale = upscale)
    BOTTOM_RIGHT = Position.grid_to_pixels("LAST_6", "LAST_2", border= 1, upscale = upscale)
    BOTTOM_LEFT = Position.grid_to_pixels("FIRST_4", "LAST_2", border = 1, upscale = upscale)
    MIDDLE_LEFT = Position.grid_to_pixels("FIRST_4", "FROM_3_TO_4", border = 1, upscale = upscale)
    
    pi.register_plugin(Calendar, TOP_HALF)
    pi.register_plugin(Timestamp, BOTTOM_RIGHT)
    pi.register_plugin(Time, BOTTOM_LEFT)
    pi.register_plugin(MemUsed, MIDDLE_LEFT)
    # pi.register_plugin(LogReader, MIDDLE_RIGHT)

    running = True
    while (running):
        logging.info(f"Checking Updates")
        pi.maybe_update_and_refresh()
        time.sleep(CONFIG["SECONDS_BETWEEN_CHECKING_UPDATES"])

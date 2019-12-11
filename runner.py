from pi import Pi
from plugins.calendar import Calendar
from plugins.timestamp import Timestamp
from position import Position
import json
import uuid
import logging

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
    
    w, h, border = 210, 50, 1
    TOP_LEFT = Position(0, 0, w, h, border, CONFIG['UPSCALE'])
    w, h, border = 75, 20, 0
    BOTTOM_RIGHT = Position(inky.WIDTH - w, inky.HEIGHT - h, w, h, border, CONFIG['UPSCALE'])

    pi.register_plugin(Calendar, TOP_LEFT)
    pi.register_plugin(Timestamp, BOTTOM_RIGHT)
    pi.maybe_update_and_refresh()

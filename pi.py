from collections import deque
import PIL 
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta
from datetime import datetime
import pickle
import os.path
import json
import re
import iso8601
from position import Position
from plugins.plugin import Plugin
import time
import logging

CONFIG = json.load(open("config.json"))
logger = logging.getLogger(__name__)

UPDATE_FREQUENCY = CONFIG['SECONDS_BETWEEN_CHECKING_UPDATES']
FLIP_VERTICALLY = True

class Pi:

    def __init__(self, inky):
        self.inky = inky
        self.display_size = inky.WIDTH * CONFIG['UPSCALE'], inky.HEIGHT * CONFIG['UPSCALE'] # Make this not dependent on UPSCALE
        self.screen = PIL.Image.new('P', self.display_size, inky.WHITE)
        self.last_updated = datetime.utcfromtimestamp(0)
        
        # plugin.name -> {plugin}
        self.plugins = {}
        self.popups = deque()  

    def register_plugin(self, plugin, position):
        try:
            self.plugins[plugin.name] = plugin(position) # Instantiate it and save it in the map with the name
            logging.info("Plugin {} Loaded - X: {} Y: {} Width: {} Height: {}".format(plugin.name, *position.get_border_box())) # Check if we can upack self params this way for position
            return True
        except Exception as e:
            logging.info(e)
            logging.info(f"ERROR in registering plugin: {plugin.name}")
            return False
    
    # Check if enought time has passed from last potential update. If so query the plugins
    def maybe_update_and_refresh(self):
        second_from_last_update = (datetime.now() - self.last_updated).total_seconds()
        logging.info(f"{second_from_last_update}s Since last update")
        if second_from_last_update >= UPDATE_FREQUENCY:
            self.pool_plugins_and_maybe_refresh()
            self.last_updated = datetime.now()
            logging.info("Pooled plugins.")

    # Obtain fresh info data from plugins, and if any is new refresh the screen. 
    def pool_plugins_and_maybe_refresh(self):
        """
        Pool all of the plugins to check if any of them has an update. (new Data or Popups)
        If so trigger the refresh of the screen. 
        This is done to minimize e-ink screen refresh as that can take up to a couple of seconds. 
        """
        need_refresh = False
        logging.info("Pooling plugins...")
        for idx, (name, plugin)  in enumerate(sorted(self.plugins.items(), key = lambda x : x[1].position.get_z_index())): 
            logging.info(f"{idx + 1}/{len(self.plugins)} Pooling: {name}")
            if plugin.check_and_store_potential_new_data():
                need_refresh = True
                popup = plugin.get_and_consume_popup()
                if popup: self.popups.extend(popup)
        
        SECONDS_BETWEEN_POPUPS = 10

        if self.popups:
            logging.info(f"N*{len(self.popups)} Popups found to process...")
            self.generate_and_refresh_screen()
            while self.popups:
                popup = self.popups.popleft()
                self.show_popup(popup)
                time.sleep(SECONDS_BETWEEN_POPUPS)
            
        if need_refresh or self.popups:
            # This also take care of removing the popups
            self.generate_and_refresh_screen()
 
    def generate_and_refresh_screen(self):
        self.generate_new_screen()
        self.refresh_screen()

    def generate_new_screen(self):
        """
        Render a new Screen Image from all the Plugins. 
        """
        logging.info("Generating Screen")
        self.screen = PIL.Image.new('P', self.screen.size, self.inky.WHITE) # Create new blank PIL Image with same size as previous one
        for name, plugin in self.plugins.items():
            logging.info(f"Generating {name} view...")
            self.add_image(plugin.render(), plugin.position)

    def refresh_screen(self):
        """
        Update the actual E-Ink Screen with the latest Image generated
        """
        logging.info("Refreshing Screen")
        to_display = self.screen.copy()
        if (FLIP_VERTICALLY):
            to_display = to_display.transpose(PIL.Image.ROTATE_180)
        to_display.thumbnail((self.inky.WIDTH, self.inky.HEIGHT), Image.ANTIALIAS) # Scale it to the Inky display size
        self.inky.set_image(to_display)
        self.inky.show()

    def show_popup(self, popup_text):
        """
        Generate and display in the middle of the Screen a new Popup based on Popup Text
        """
        logging.info(f"Processing Popup: {popup_text}")
        popup = Popup([popup_text], (self.inky.WIDTH, self.inky.HEIGHT))
        self.add_image(popup.render(), popup.position)
        self.refresh_screen()

    def add_image(self, img, position):
        """
        Add a PIL Image in a given position over the background.
        """        
        logging.info(f"Adding IMG - ({img.size}) in position {position.get_bounding_box()}")
        background = self.screen
        if position.border:
            # Render a border as background
            PIL.ImageDraw.Draw(background).rectangle(position.get_bounding_box(), fill = self.inky.WHITE)
        background.paste(img, (position.get_content_box()[:2]))


class Popup(Plugin):

    name = "POPUP"
    width, height = 120, 35
    border_size = 2

    def __init__(self, text, parent_size):
        middle_x, middle_y = tuple(x // 2 for x in parent_size)
        start_x, start_y = middle_x - (Popup.width // 2), middle_y - (Popup.height // 2)
        centered_pos = Position(start_x, start_y, Popup.width, Popup.height, self.border_size, CONFIG['UPSCALE'])

        super(Popup, self).__init__(centered_pos)

        self.position = centered_pos
        self.last_data = text

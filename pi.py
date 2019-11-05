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
import uuid
import logging

CONFIG = json.load(open("config.json"))
logger = logging.getLogger(__name__)
UPDATE_FREQUENCY = 60 * 3
TIME_BETWEEN_POPUPS = 10

# 212x104 

class Pi:
    
    def __init__(self, inky):
        self.inky = inky
        self.screen = PIL.Image.new('RGB', (212 * 2, 104 * 2), tuple(CONFIG['BACKGROUND_COLOR_RGB'])) #TODO Make it get the size from Inky inky.size)
        self.last_updated = datetime.utcfromtimestamp(0)
        
        # plugin.name -> {plugin}
        self.plugins = {}
        self.popups = deque()  
    
    def register_plugin(self, plugin, position):
        try:
            self.plugins[plugin.name] = plugin(position) # Instantiate it and save it in the map with the name
            ## Maybe we could assert that position fit in the Inky and that it has the methods we expect. Inherithance maybe?
            logging.info("Plugin {} Loaded - X: {} Y: {} Width: {} Height: {}".format(plugin.name, *position.get_border_box())) # Check if we can upack self params this way for position
            return True
        except Exception as e:
            logging.info(e)
            print("ERROR in registering plugin: {} ".format(plugin.name))
            return False
    
    # Check if enought time has passed from last potential update. If so query the plugins
    def maybe_update_and_refresh(self):
        from_last_update = datetime.now() - self.last_updated
        logging.info("{}s Since last update".format(from_last_update.total_seconds()))
        if from_last_update.total_seconds() >= UPDATE_FREQUENCY:
            self.pool_plugins_and_maybe_refresh()
            self.last_updated = datetime.now()
            logging.info("POOLED")
    
    # Obtain fresh info data from plugins, and if any is new refresh the screen. 
    def pool_plugins_and_maybe_refresh(self):
        need_refresh = False
        logging.info("Pooling plugins")
        for idx, (name, config)  in enumerate(sorted(self.plugins.items(), key = lambda x : x[1].position.get_z_index())): 
            logging.info("{}/{} Pooling: {}".format(idx + 1, len(self.plugins), name))
            if config.check_and_store_potential_new_data(): # There was new data
                need_refresh = True
                popup = config.get_and_consume_popup()
                if popup: self.popups.append(popup)
                
        if self.popups:
            logging.info("Popup found")
            self.generate_and_refresh_screen()
            while self.popups:
                popup = self.popups.popleft()
                logging.info("Processing popup: {}".format(popup))
                self.show_popup(popup)
                time.sleep(TIME_BETWEEN_POPUPS)
            
        if need_refresh or self.popups:
            # This also take care of removing the popups
            self.generate_and_refresh_screen()
                
    def generate_and_refresh_screen(self):
        self.generate_new_screen()
        self.refresh_screen()
         
    def generate_new_screen(self):
        logging.info("Generating Screen")
        self.screen = PIL.Image.new('RGB', self.screen.size, tuple(CONFIG['BACKGROUND_COLOR_RGB'])) # Create new blank PIL Image with same size as previous one
        for name, plugin in self.plugins.items():
            logging.info("Generating {} view...".format(name))
            self.add_image(plugin.render(), plugin.position)
            # Update the PIL Image with the plugins stuff, check if we want a border as well. That could be coool

    def refresh_screen(self):
        logging.info("Refreshing Screen")
        self.screen.save("img/" + uuid.uuid4().hex + ".png")
        # imshow(self.screen, cmap='gray')
        # self.inky.display(self.screen)
    
    def show_popup(self, popup):
        middle = 212//2 * 2, 104//2 * 2
        start = middle[0] - Popup.SIZE[0] // 2, middle[1] - Popup.SIZE[1] // 2
        pos = Position(start[0] , start[1], Popup.SIZE[0], Popup.SIZE[1], 2)
        self.add_image(Popup(popup, pos).render(), pos)
        self.refresh_screen()

    def add_image(self, img, position):
        logging.info("Adding IMG in position {}".format(position.get_bounding_box()))
        background = self.screen
        if position.border:
            # Render a border as background
            PIL.ImageDraw.Draw(background).rectangle(position.get_bounding_box(), fill = tuple(CONFIG['TEXT_COLOR']))
        background.paste(img, (position.get_content_box()[:2]))


class Popup(Plugin):

    name = "POPUP"
    SIZE = (100 * 2, 30 * 2)   

    def __init__(self, text, position):
        super.__init__(position)
        self.last_data = text

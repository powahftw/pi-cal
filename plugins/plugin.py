import json
import PIL 
from PIL import Image, ImageDraw, ImageFont
import logging
from font_fredoka_one import FredokaOne

CONFIG = json.load(open("config.json"))
logger = logging.getLogger(__name__)

import sys
sys.path.append("..") # Adds higher directory to python modules path.
from position import Position

class Plugin():
    
    FONT = ImageFont.truetype(FredokaOne, 12 * CONFIG['UPSCALE'])

    def __init__(self, position):
        self.position = position # Position (start_X, start_Y, width, height, border)
        self.last_data = []
        self.last_popup = []
    
    def get_and_consume_popup(self):
        # TODO Finish implementation that support nicely multiple popups.
        popup = self.last_popup
        self.last_popup = [] # Consume popup
        return popup

    def check_and_store_potential_new_data(self):
        logger.info(type(self))
        data, popups = self.update()
        if popups or data != self.last_data:
            self.last_data, self.last_popup = data, popups
            return True
        return False
    
    @staticmethod
    def fit_text(line, max_width, fit_mode, font_size):

        MINIMUM_FONT_SIZE = 2

        logger.info(f"\nFitting text:\n{line}\nMODE: {fit_mode}")
        if fit_mode == 0: return line
        line_w, _ = Plugin.FONT.getsize(line)
        if line_w < max_width: return line
        # TODO Performance issue with long lines, should do a binary search
        while line_w >= max_width and line and font_size > MINIMUM_FONT_SIZE:
            if fit_mode == 1:
                line = line[:-1] # Remove last char
                line_w, _ = Plugin.FONT.getsize(line + "..")
            elif fit_mode == 2:
                font_size -= 0.5
                line_w, _ = Plugin.FONT.getsize(line)
        # If we had to delete stuff from the string, so we need to elipsize
        if fit_mode == 1: line += ".." 
        logger.info(f"FITTED LINE: {line}")
        return line
                 
    # TODO Fit_Mode to convert to enum
    # 0 do nothing, 1 elipsize text, 2 reduce font to fit.
    def render_lines(self, lines, position, fit_mode = 1, font_size = 12):
        OFFSET_LEFT, curr_h = 3, 3
        _, _, max_w, max_h = self.position.get_content_box()
        txt_img = PIL.Image.new('P', (max_w, max_h), tuple(CONFIG['BACKGROUND_COLOR_RGB']))
        text_on = PIL.ImageDraw.Draw(txt_img)
        for line in lines:
            logger.info(f"CURR_H {curr_h}, MAX_H {max_h}")
            fitted_line = Plugin.fit_text(line, max_w - OFFSET_LEFT, fit_mode, font_size)
            _, line_h = self.FONT.getsize(fitted_line)
            if curr_h + line_h > max_h: break
            text_on.text((OFFSET_LEFT, curr_h), fitted_line,
                         font = self.FONT, fill = tuple(CONFIG['TEXT_COLOR']))
            curr_h += line_h # Assuming vertical spacing is already embedded in drawed_line
                             # TODO Constant spacing actually looks better...
        return txt_img
    
    # Common method 
    def render(self):
        return self.render_lines(self.last_data, self.position)  
    
    # Return new data, potentially popups. Will be overridden by subclasses
    def update(self):
        return [""], ["ERROR, Update not defined"]
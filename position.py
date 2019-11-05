
class Position():
    # Position information of a plugin. Offset from top left. Width and Height include the border size.
    def __init__(self, start_X, start_Y, width, height, border = 0, z_index = 0):
        self.start_X, self.start_Y = start_X, start_Y
        self.width, self.height = width, height
        self.border, self.z_index = border, z_index
    
    def get_content_box(self):
        return (self.start_X + self.border, self.start_Y + self.border,
                self.width - 2 * self.border, self.height - 2 * self.border)
    
    def get_border_box(self):
        return (self.start_X, self.start_Y,
                self.width, self.height)
    
    def get_bounding_box(self):
        return (self.start_X, self.start_Y, self.start_X + self.width - 1, self.start_Y + self.height - 1)
    
    def get_z_index(self):
        return self.z_index
    

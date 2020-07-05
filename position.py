
class Position():
    # Position information of a plugin. Offset from top left. Width and Height include the border size.
    def __init__(self, start_X, start_Y, width, height, border = 0, upscale = 1, z_index = 0):
        self.start_X, self.start_Y = start_X * upscale, start_Y * upscale
        self.width, self.height = width * upscale, height * upscale
        self.border, self.z_index = border * upscale, z_index
    
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

    """
    Supported patterns:
        FIRST_X
        LAST_X
        FROM_X_TO_Y
    By default columns are 21px wide, rows are 17px wide.
    """
    @staticmethod
    def grid_to_pixels(x, y, maxx = 212, maxy = 104, divx = 10, divy = 6, padding = 1, border = 0, upscale = 1, z_index = 0):
        def parse(str_value, max_value, chunk_size):
            op, *args = str_value.split("_")
            if op == "FIRST":
                from_px, chunk_n = 0, int(args[0])
            elif op == "LAST":
                last_px = int(args[0]) * chunk_size
                from_px, chunk_n = max_value - last_px - 1, int(args[0])
            elif op == "FROM":
                last_px = int(args[0]) * chunk_size
                from_px, chunk_n = max_value - last_px - 1, int(args[2]) - int(args[0])
            else: raise ValueError(f"Unsupported operator {op}")
            print(from_px, chunk_n * chunk_size)
            return max(from_px, padding), chunk_n * chunk_size
        column_size, row_size = int((maxx - 2 * padding) / divx), int((maxy - 2 * padding) / divy)
        x0, dx = parse(x, maxx, column_size)
        y0, dy = parse(y, maxy, row_size)
        return Position(x0, y0, dx, dy, border, upscale, z_index)

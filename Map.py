class Tile:
    #A tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        self.explored = False

        #by default if a tile is blocked it also blocks sight
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


class Rect:
    #A rectangle on the map. used to characterize a aroom
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) //2
        center_y = (self.y1 + self.y2) //2
        return(center_x, center_y)

    def intersect(self, other):
        #returns true if this rectangle intersects with another
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

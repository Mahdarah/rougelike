from GameObject.Fighter import Fighter
from GameObject.enemies.BasicMonster import BasicMonster
from GameObject.items.Item import Item
import Map
class GameObject():
    #A generic object, could be: the player, a monster, an item, the stairs
    #always represented by an ASCII character on screen.
    def __init__(self, x, y, char,name, color, blocks=False,fighter=None, ai=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks

        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.item = item
        if self.item: # let component know who owns it
            self.item.owner = self
        print("my name is " + self.name)
    def move(self, dx, dy):
        global healtime
        global TORCH_RADIUS
        #move by given amount
        tuny = 0
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            if self == player:
                if healtime > -1:
                    #message(str(healtime),colors.yellow)
                    healtime -=1
        #else: ((IF WALKING INTO WALL))
            #if self == player:
            #    tuny -= 1
            #    message(str(tuny),colors.red)

    def move_towards(self,target_x,target_y):
        #vector from this object to the taget and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1(preserving direction ), then round it and
        #convert it to integer, so movement is restricted to map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx,dy)

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self):
        #make this drawn first, so all others are drawn over it
        global objects
        objects.remove(self)
        objects.insert(0,self)

    def draw(self):
        global visible_tiles
        #only show if visible to player
        if (self.x, self.y) in visible_tiles:
            #Draw the ASCII character that represents this object at its position
            con.draw_char(self.x, self.y, self.char, self.color, bg=None)

    def clear(self):
        #erase ASCII character that represents this object
        con.draw_char(self.x, self.y, ' ', self.color, bg=None)
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

#these are dungeon generation
def is_blocked(x,y):

    if my_map[x][y].blocked:
        return True

    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True

def create_room(room):
    global my_map
    #go through the tiles in the rectangle and make them passsable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            my_map[x][y].blocked = False
            my_map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
    global my_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global my_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False

def is_visible_tile(x, y):
    global my_map

    if x >= MAP_WIDTH or x < 0:
        return False
    elif y >= MAP_HEIGHT or y < 0:
        return False
    elif my_map[x][y].blocked == True:
        return False
    elif my_map[x][y].block_sight == True:
        return False
    else:
        return True


def make_map():
    global my_map
    #fill map with "blocked" tiles
    my_map = [[Tile(True) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        #random width and height
        w = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of map boundries
        x = randint(0, MAP_WIDTH-w-1)
        y = randint(0, MAP_HEIGHT-h-1)

        #Rect makes rectangles easier to work with
        new_room = Rect(x,y,w,h)

        #run through the other rooms to see if they intersects
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            #if no intersections, I.E a valid room

            #paint it to the maps tiles
            create_room(new_room)

            #center coords of room
            (new_x, new_y) = new_room.center()

            if num_rooms == 0:
                #first room, where player starts
                player.x = new_x
                player.y = new_y

            else:
                #for all rooms after first: connect to previous with tunnel

                #center coords of prev. room
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                #coin flip!
                if randint(0,1):
                    #move horizontally first
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #move vertically first
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x,new_x,new_y)

            #add contets to room, such as monsters
            place_objects(new_room)

            #append the new room to list
            rooms.append(new_room)
            num_rooms += 1

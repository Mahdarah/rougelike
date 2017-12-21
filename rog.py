import tdl
from random import randint
import colors
import math
import textwrap
#important  variables. CAPITAL so you know that they won't change.
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
#GUI STUFF
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

MAP_WIDTH = 80
MAP_HEIGHT = 43

ROOM_MAX_SIZE = 30 #defualt for tutorial was 10 and 6
ROOM_MIN_SIZE = 2
MAX_ROOMS = 80

FOV_ALGO = 'BASIC' #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

MAX_ROOM_MONSTERS = 3

LIMIT_FPS = 20

color_dark_wall = colors.darkwall
color_dark_floor = colors.darkfloor
color_light_wall = colors.lightwall
color_light_floor = colors.lightfloor


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


class GameObject:
    #A generic object, could be: the player, a monster, an item, the stairs
    #always represented by an ASCII character on screen.
    def __init__(self, x, y, char,name, color, blocks=False,fighter=None, ai=None):
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

    def move(self, dx, dy):
        #move by given amount
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

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

class Fighter:
    #combat related properties
    def __init__(self,hp,defense,power,death_function):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function


    def take_damage(self,damage):
        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        #simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            message(self.owner.name.capitalize() + ' attacks ' + target.name+ ' for '+str(damage), colors.lighter_han)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize()+ ' attacks ' + target.name+ ' but it had no effect')





class BasicMonster:
    #AI for a basic monster
    def take_turn(self):
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:

            if monster.distance_to(player) >=2:
                monster.move_towards(player.x,player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

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

def place_objects(room):
    #choose random number of monsters
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        #choose random spot for monster
        x = randint(room.x1,room.x2)
        y = randint(room.y1,room.y2)

        #only place if tile is not blocked
        if not is_blocked(x,y):
            if randint(0,100) < 90:  #80% chance of getting an orc
                #create an orc
                ranpow = randint(3,6)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'o','orc',colors.orcgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)
            else:
                #create a troll
                ranpow = randint(5,8)
                randen = randint(1,4)
                ranhp = randint(6,13)
                fighter_component = Fighter(hp=ranhp, defense=randen,power=ranpow,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'T','troll',colors.trollgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)

            objects.append(monster)
            #########################################
            #CODE FOR MORE MONSTErS
            #########################################
            #chances: 20% monster A, 40% monster B, 10% monster C, 30% monster D:
            #choice = randint(0, 100)
            #if choice < 20:
            #    #create monster A
            #elif choice < 20+40:
            #    #create monster B
            #elif choice < 20+40+10:
            #    #create monster C
            #else:
            #    #create monster D

def render_bar(x,y,total_width,name,value,maximum,bar_color,back_color):
    #render a bar(hp,mana,etc). Fist calculate width of the bar
    bar_width = int(float(value) / maximum * total_width)

    #render background first
    panel.draw_rect(x,y,total_width, 1, None,bg=back_color)

    #render bar on top
    if bar_width > 0:
        panel.draw_rect(x,y,bar_width,1,None,bg=bar_color)

    #centered text with the values
    text = name + ': ' + str(value) + '/' + str(maximum)
    x_centered = x + (total_width-len(text))//2
    panel.draw_str(x_centered,y,text,fg=colors.white,bg=None)

def get_names_under_mouse():
    #return string with the names of all objects under the mouse
    (x,y) = mouse_coord

    #create a list with the names of all the objects at mouse coord and in FOV
    names = [obj.name for obj in objects if obj.x == x and obj.y == y and
    (obj.x, obj.y) in visible_tiles]

    names = ', '.join(names) #join names seperated by commas
    return names.capitalize()

def render_all():

    global fov_recompute
    global visible_tiles

    if fov_recompute:
        fov_recompute = False
        visible_tiles = tdl.map.quickFOV(player.x, player.y,
                                         is_visible_tile,
                                         fov=FOV_ALGO,
                                         radius=TORCH_RADIUS,
                                         lightWalls=FOV_LIGHT_WALLS)

    #draw all objects in the list
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = (x,y) in visible_tiles
            wall = my_map[x][y].block_sight
            if not visible:

                if my_map[x][y].explored:
            #it's out of the player's FOV
                    if wall:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_wall)
                    else:
                        con.draw_char(x, y, None, fg=None, bg=color_dark_floor)

            else:
                #if in players FOV
                if wall:
                    con.draw_char(x,y,None,fg=None,bg=color_light_wall)
                else:
                    con.draw_char(x,y,None,fg=None,bg=color_light_floor)
                #since its visible, explore it
                my_map[x][y].explored = True

    for obj in objects:#DRAW PLAYER LAST SO IT IS ALWAYS ON TOP
        if obj != player:
            obj.draw()
    player.draw()
    if player.fighter.hp < 0:
        player.fighter.hp = 0

    if player.fighter.hp > player.fighter.max_hp:
        player.fighter.hp = player.fighter.max_hp
        
    #prepare to render the GUI panel
    panel.clear(fg=colors.white, bg=colors.black)

    #pring game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        panel.draw_str(MSG_X, y, line, bg=None, fg=color)
        y += 1

    #show players stats
    render_bar(1,1,BAR_WIDTH,'HP',player.fighter.hp,player.fighter.max_hp,
    colors.light_red,colors.darker_red)

    #display names of objects under mouse
    panel.draw_str(1,0,get_names_under_mouse(), bg=None, fg=colors.light_grey)

    #blit the cpmtemts of con to the root console and present it
    root.blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)
    root.blit(panel, 0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0)

def message(new_msg,color = colors.white):
    #split the message if necessary, amoung multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        #if the buffer is full remove the first line to make room for new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        #add new line as a tuple with text and color
        game_msgs.append((line, color))

def player_move_or_attack(dx,dy):
    global fov_recompute

    #coordinats player is attacking
    x = player.x + dx
    y = player.y + dy

    #look for attackable object there
    target = None
    for obj in objects:
        if obj.fighter and obj.x == x and obj.y == y:
            target = obj
            break

    #attack if target found, otherwise move
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx,dy)
        fov_recompute = True
#Check for pressed key then change coordinates
def handle_keys():
    global playerx, playery
    global fov_recompute
    global mouse_coord
    user_input = tdl.event.key_wait()

    keypress = True
    for event in tdl.event.get():
        if event.type == 'KEYDOWN':
            user_input = event
            keypress = True
        if event.type == 'MOUSEMOTION':
            mouse_coord = event.cell

    if not keypress:
        return 'Didnt-take-turn' #ADD TUTORIAL AT SOME POINT MAybe?

    #Shortcut for fullscreen and for exiting game
    if user_input.key == 'ENTER' and user_input.alt:
        #If enter AND alt, toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    elif user_input.key == 'ESCAPE':
        return 'exit'

    if game_state == 'playing':
        #Movement keys
        if user_input.key == 'UP':
            player_move_or_attack(0,-1)


        elif user_input.key == 'DOWN':
            player_move_or_attack(0,1)


        elif user_input.key == 'LEFT':
            player_move_or_attack(-1,0)


        elif user_input.key == 'RIGHT':
            player_move_or_attack(1,0)

        else:
            return 'turn-not-taken'

def player_death(player):
    #the game has ended
    global game_state
    message('You have died.',colors.red)
    game_state = 'dead'

    player.color = colors.darker_red

def monster_death(monster):
    #transform into corpse
    message(monster.name.capitalize() + ' is dead!', colors.amber)
    monster.char = '%'
    monster.color = colors.darker_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of' + monster.name
    monster.send_to_back()

#############################################
# Initialization & Main Loop                #
#############################################


#setting font
tdl.set_font('arial10x10.png',greyscale=True , altLayout=True)

#initilize window
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="ROG",fullscreen=False)
tdl.setFPS(LIMIT_FPS)
con = tdl.Console(SCREEN_WIDTH,SCREEN_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)


fighter_component = Fighter(hp=50, defense=2, power=5,death_function=player_death)
player = GameObject(SCREEN_WIDTH//2,SCREEN_HEIGHT//2,'@','player',colors.white,blocks=True,
fighter=fighter_component)


objects = [player]

make_map()

fov_recompute = True

game_state = 'playing'
player_action = None

game_msgs = []

message('Try your best.',colors.light_sky)
mouse_coord = (0,0)
#Main Loop
while not tdl.event.is_window_closed():
    #Draw all objects
    render_all()

    tdl.flush() #this presents change to the screen

    #erase all objects
    for obj in objects:
        obj.clear()
    #handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    if game_state == 'playing' and player_action != 'turn-not-taken':
        for obj in objects:
            if obj.ai:
                obj.ai.take_turn()

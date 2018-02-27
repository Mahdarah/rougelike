import tdl
from random import randint
from tcod import image_load
import colors
import math
import textwrap
import shelve

#important  variables..
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
#GUI STUFF
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

MAX_ROOM_ITEMS = 3

MAP_WIDTH = 80
MAP_HEIGHT = 43
#this is a comment
ROOM_MAX_SIZE = 30 #defualt for tutorial was 10 and 6
ROOM_MIN_SIZE = 2
MAX_ROOMS = 80

FOV_ALGO = 'BASIC' #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

MAX_ROOM_MONSTERS = 3

healtime = 0

LIMIT_FPS = 20

XP = 0
MAX_XP = 100

HEAL_AMOUNT = 4

SKILLPOINTS = 0

#Spell values!
LIGHTNING_RANGE = 5
LIGHTNING_DAMAGE = 20
CONFUSE_NUM_TURNS = randint(8,15)
CONFUSE_RANGE = 8

INVENTORY_WIDTH = 50

horizontalstart = []
horizontalend = []
verticalstart = []
verticalend = []

color_dark_wall = colors.darkwall
color_dark_floor = colors.darkfloor
color_light_wall = colors.lightwall
color_light_floor = colors.lightfloor

#####################################
#ABILITIES                          #
#####################################
HEALABL = False

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

class Fighter:
    #combat related properties
    def __init__(self,hp,defense,power,xpgain,death_function):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
        self.xpgain = xpgain


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
            message(self.owner.name.capitalize() + ' attacks ' + target.name+ ' for '+str(damage), target.color )#colors.lighter_han)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize()+ ' attacks ' + target.name+ ' but it had no effect')

    def heal(self,amount):
        #heal given amount without going over maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp



class BasicMonster:
    #AI for a basic monster
    def take_turn(self):
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:

            if monster.distance_to(player) >=2:
                monster.move_towards(player.x,player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

class ConfusedMonster:
    #AI for a confused monster
    def __init__(self,old_ai,num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0: #if still confused
            #move in random direction & decrease amount of turns confused
            self.owner.move(randint(-1,1),randint(-1,1))
            self.num_turns -= 1

        else: #restore previous AI
            self.owner.ai = self.old_ai
            message('The '+ self.owner.name + ' is no longer confused!', colors.orange)

class Item:
    #iitem that can be picked up and used
    def __init__(self,use_function=None):
        self.use_function = use_function

    def pick_up(self):
        #add to players inv, remove from map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up the' + self.owner.name +'!', colors.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up the ' + self.owner.name + '!', colors.light_purple)

    def drop(self):
         #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', colors.yellow)

    def use(self):
        #call the use_function if defined
        if self.use_function is None:
            message('The '+self.owner.name+' cannot be used!')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner) #destroy after use, unless cancelled(e.g. trying to use health potion when health is full)
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
    horizontalstart.append(x1)
    horizontalend.append(x2)
    global my_map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False
    return horizontalstart
    return horizontalend


def create_v_tunnel(y1, y2, x):
    verticalstart.append(y1)
    verticalend.append(y2)
    global my_map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        my_map[x][y].blocked = False
        my_map[x][y].block_sight = False
    return verticalstart
    return verticalend

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
    global my_map, objects, horizontalstart, horizontalend, num_rooms, rooms, DOWNSTAIR, mandatory_list, mandatory_number
    DOWNSTAIR = 1

    mandatory_list = [DOWNSTAIR]
    mandatory_number = sum(mandatory_list)

    objects = [player]
    #fill map with "blocked" tiles
    my_map = [[Tile(True) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

    rooms = []
    #print(rooms)
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
            #hallway or room?
            if randint(0,100) <= 75:
                place_objects(new_room)
            else:
                if horizontalstart:
                    randomstart = randint(0,len(horizontalstart)-1)
                    print(horizontalstart)
                    #print("howdy"+str(randomstart))
                    if horizontalend:
                        print(horizontalend)
                        if horizontalstart[randomstart] < horizontalend[randomstart]:
                            #print("TeSTING 1")
                            randomhspot = randint(horizontalstart[randomstart],horizontalend[randomstart])
                        else:
                            #print("ISITONLYNOW?")
                            randomhspot = randint(horizontalend[randomstart],horizontalstart[randomstart])
                    else:
                        make_map()
                else:
                    make_map()
                #newhtunnel =
                place_objects(new_room)
            #append the new room to list
            rooms.append(new_room)
            num_rooms += 1

skipme = 1
def place_objects(room):
    global num_rooms, rooms, DOWNSTAIR

    #choose random number of monsters
    num_monsters = randint(0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        #choose random spot for monster
        x = randint(room.x1+1, room.x2-1)
        y = randint(room.y1+1, room.y2-1)

        #only place if tile is not blocked
        if not is_blocked(x,y):
            choice = randint(0,100)
            if choice < 40:  #40% chance of getting an orc
                #create an orc
                ranpow = randint(3,6)
                randen = 1
                ranhp = 5
                ranxp = math.floor(ranpow+randen+(ranhp/2) /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'o','orc',colors.orcgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)
            elif choice < 40+15: #15% chance
                #create a troll
                ranpow = randint(5,8)
                randen = randint(1,4)
                ranhp = randint(6,13)

                ranxp = math.floor(ranpow+randen+(ranhp/2) /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'T','troll',colors.trollgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)

            elif choice < 40+5+2: #2% chance
                #Create a gark
                ranhp = randint(2,4)
                randen = randint(2,3)
                ranpow = randint(2,6)
                ranxp = math.floor(ranpow+randen+(ranhp/2) /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'G','gark',colors.goblingreen, blocks=True,
                fighter=fighter_component, ai=ai_component)
            else:
                #Create a goblin
                ranhp = randint(2,60)
                randen = randint(0,1)
                ranpow = randint(1,4)
                ranxp = math.floor(ranpow+randen+(ranhp/2) /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'g','goblin',colors.goblingreen, blocks=True,
                fighter=fighter_component, ai=ai_component)


            objects.append(monster)
    ########################
    #END MONSTER START ITEM#
    ########################

    num_items = randint(0,MAX_ROOM_ITEMS)

    for i in range(num_items):
            #choose random spot for this item
        x = randint(room.x1+1, room.x2-1)
        y = randint(room.y1+1, room.y2-1)

        dice = randint(0,100)

        if dice < 70:
                        #create a healing potion
                        item_component = Item(use_function=cast_heal)
                        item = GameObject(x, y, '!', 'healing potion', colors.violet,
                                          item=item_component)

        elif dice < 70+10:
                        #create a confusion scroll 10% chance
                        item_component = Item(use_function=cast_confuse)

                        item = GameObject(x,y,'#','scroll of confusion',colors.light_yellow,item=item_component)
        else:
                        #create a lightning scroll
                        item_component = Item(use_function = cast_lightning)

                        item = GameObject(x,y,"#",'scroll of lightning bolt',colors.light_yellow, item=item_component)



        objects.append(item)
        item.send_to_back() #items appear below other objects


    for i in range(mandatory_number):
        global skipme
        #print(mandatory_number)
        if skipme == 0:
        #    print("HOLLY")
            if num_rooms > 2:
            #    print("LOPUYEAH")
                #print(num_rooms)
                #print(rooms)
                roomtarget = rooms[randint(0+1,num_rooms-1)]
                x = randint(roomtarget.x1+1, roomtarget.x2-1)
                y = randint(roomtarget.y1+1, roomtarget.y2-1)

                dice = randint(0,mandatory_number)

                if dice == 1:
                    if DOWNSTAIR > 0:
                        mandatory = GameObject(x,y,">","Down stairs",colors.red)
                        DOWNSTAIR -= 1
                        objects.append(mandatory)
                        print("STARES PLACFED")
                        #print(x)
                        #print(y)
                    else:
                        print("XGUNNAGIVEITTOYA")
                        dice += 1


        else:
            skipme -= 1
            print(skipme)



def render_bar(x,y,total_width,name,value,maximum,bar_color,back_color,text_color):
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
    panel.draw_str(x_centered,y,text,fg=text_color,bg=None)


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
    colors.hpcolor,colors.darker_red,colors.black)

    render_bar(1,2,BAR_WIDTH,'XP',XP,MAX_XP,colors.xpamber,colors.darker_xpamber,colors.black)


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

def menu(header,options,width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options')
    header_wrapped = []
    for header_line in header.splitlines():
        header_wrapped.extend(textwrap.wrap(header_line, width))

    header_height = len(header_wrapped)
    height = len(options) + header_height

    #create an off-screen console that represents the menu's window
    window = tdl.Console(width,height)

    #print header with wrapped text
    window.draw_rect(0,0,width,height,None,fg=colors.white,bg=None)
    for i, line in enumerate(header_wrapped):
        window.draw_str(0,0+i,header_wrapped[i])

    y = header_height
    letter_index = ord('a') #this returns ASCII code of "a"
    for option_text in options:
        text = '('+chr(letter_index) + ')  ' + option_text
        window.draw_str(0,y,text,bg=None)
        y += 1
        letter_index += 1

    #blit contents of window to root
    x = SCREEN_WIDTH//2 - width//2
    y = SCREEN_HEIGHT//2 - height//2
    root.blit(window,x,y,width,height,0,0)

    #present root and wait for key press
    tdl.flush()
    key = tdl.event.key_wait()
    key_char = key.char
    if key_char == '':
        key_char = ' ' #placeholder

    if key.key == 'ENTER' and key.alt:
        #toggle fullscreen
        tdl.set_fullscreen(not tdl.get_fullscreen())

    #convert ASCII code to an index, if it corrosponds to option, return it
    index = ord(key_char) - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def inventory_menu(header):
    #show menu with inventory as option
    if len(inventory) == 0:
        options = ['Inventory is empty']
    else:
        options = [item.name for item in inventory]

    index = menu(header,options,INVENTORY_WIDTH)

    #if an item was chosen, return it
    if index is None or len(inventory) == 0:
        return None
    return inventory[index].item

def msgbox(text,width=50):
    menu(text,[],width) #use menu as a message box

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

        #######################################
        #               OTHER KEYS            #
        #######################################


        #elif user_input.text == 'h':
            #message('OHNO', colors.red)
            #heal()

        elif user_input.text == 'g':
            #pick up an item
            for obj in objects: #look for an item in current tile
                if obj.x == player.x and obj.y == player.y and obj.item:
                    obj.item.pick_up()
        elif user_input.text == 'i':
            #show inventory
            chosen_item = inventory_menu('\nPress the key next to an item to use it, or any other to cancel. \n')
            if chosen_item is not None:
                chosen_item.use()

        elif user_input.text == 'd':
            #show inventory, if item selected, drop it
            chosen_item = inventory_menu('\nPress the key next to an item to drop it, or any other to cancel. \n')
            if chosen_item is not None:
                chosen_item.drop()

        else:
            return 'turn-not-taken'

#def heal():
#    global healtime
#    global HEALABL
#    if healtime <= 0:
    #    if HEALABL:
        #    if player.fighter.hp < player.fighter.max_hp:
            #    healtime = 100
                #player.fighter.hp += player.fighter.max_hp//2

def player_death(player):
    #the game has ended
    global game_state
    message('You have died.',colors.red)
    game_state = 'dead'

    player.color = colors.darker_red
def xpfun():
    global XP
    global MAX_XP
    global SKILLPOINTS
    if XP > MAX_XP:
        XP -= MAX_XP
        half = MAX_XP // 2
        MAX_XP += math.floor(half)
        SKILLPOINTS += 1
        message(str(SKILLPOINTS),colors.yellow)




def monster_death(monster):
    global XP
    #transform into corpse
    message(monster.name.capitalize() + ' is dead! Gained '+str(monster.fighter.xpgain)+' xp', colors.xpamber)
    monster.char = '%'
    monster.color = colors.darker_red
    monster.blocks = False
    XP += monster.fighter.xpgain
    xpfun()
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of' + monster.name
    monster.send_to_back()

def closest_monster(max_range):
    #find closest enemy in range and in players FOV
    closest_enemy = None
    closest_dist = max_range + 1 #start with slightly more than max range

    for obj in objects:
        if obj.fighter and not obj == player and (obj.x,obj.y) in visible_tiles:
            #calculate distance between this object and player
            dist = player.distance_to(obj)
            if dist < closest_dist: #its closer so remember it
                closest_enemy = obj
                closest_dist = dist

    return closest_enemy

def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('Your health is full!',colors.red)
        return 'cancelled'

    message('You feel stronger',colors.dark_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    #find closest enemy in range and do damage to it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message('No enemy is close enough', colors.red)
        return 'cancelled'

    #ZAPPPP
    message('A lightning bolt strikes the '+monster.name+' with a loud crash! ' +str(LIGHTNING_DAMAGE) + ' damage was delt.', colors.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confuse():
    #find closest monster and make it confused
    monster = closest_monster(CONFUSE_RANGE)
    if monster is None: #no enemy in max range
        message('No enemy is close enough', colors.red)
        return 'cancelled'

    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster #tell new component who owns it
    message('The eyes of the '+monster.name+' grow cloudy', colors.light_blue)

def new_game():
    global player, inventory, game_msgs, game_state
    #create object representing player
    fighter_component = Fighter(hp=100, defense=2, power=5,xpgain=0,death_function=player_death)
    player = GameObject(SCREEN_WIDTH//2,SCREEN_HEIGHT//2,'@','player',colors.white,blocks=True,fighter=fighter_component)

    #generate map
    make_map()

    game_state = 'playing'

    inventory = []
    game_msgs = []
    del horizontalstart[:]
    del horizontalend[:]
    del verticalstart[:]
    del verticalend[:]

    message('Try your best.',colors.light_sky)

def save_game():
    #open a new shelve to store game data
    with shelve.open('savegame','n') as savefile:
        savefile['my_map'] = my_map
        savefile['objects'] = objects
        savefile['player_index'] = objects.index(player)  #index of player in objects list
        savefile['inventory'] = inventory
        savefile['game_msgs'] = game_msgs
        savefile['game_state'] = game_state

def load_game():
    #open saved shelf and load game data
    with shelve.open('savegame','r') as savefile:
        my_map = savefile['my_map']
        objects = savefile['objects']
        player = objects[savefile['player_index']]  #get index of player in objects list and access it
        inventory = savefile['inventory']
        game_msgs = savefile['game_msgs']
        game_state = savefile['game_state']

def play_game():
    global fov_recompute

    player_action = None
    fov_recompute = True
    con.clear() #unexplored areas start with black

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
            save_game()
            break

        if game_state == 'playing' and player_action != 'turn-not-taken':
            for obj in objects:
                if obj.ai:
                    obj.ai.take_turn()

def main_menu():
    img = image_load('background.png')

    while not tdl.event.is_window_closed():
        #show background image at twice regular console resolution
        img.blit_2x(root,0,0)

        #show games title and credits
        title = 'THIS GAME HAS NO NAME YET'
        center = (SCREEN_WIDTH - len(title)) //2
        root.draw_str(center, SCREEN_HEIGHT//2-6,title,bg=None,fg=colors.light_red)

        title = 'By Mahdarah'
        center = (SCREEN_WIDTH - len(title)) //2
        root.draw_str(center, SCREEN_HEIGHT//2-4,title,bg=None,fg=colors.light_red)

        #show options and wait for players choice
        choice = menu('',['New game','Continue game','Quit'],24)

        if choice == 0: #new game
            new_game()
            play_game()
        elif choice == 1: #load game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()

        elif choice == 2: #quit
            break


#############################################
# Initialization & Main Loop                #
#############################################

#setting font
tdl.set_font('arial10x10.png',greyscale=True , altLayout=True)

#initilize window
root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Esper",fullscreen=False)
tdl.setFPS(LIMIT_FPS)
con = tdl.Console(SCREEN_WIDTH,SCREEN_HEIGHT)
panel = tdl.Console(SCREEN_WIDTH, PANEL_HEIGHT)

main_menu()

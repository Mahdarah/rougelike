def place_objects(room):
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
                ranxp = math.floor(ranpow+randen+ranhp /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'o','orc',colors.orcgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)
            elif choice < 40+15: #15% chance
                #create a troll
                ranpow = randint(5,8)
                randen = randint(1,4)
                ranhp = randint(6,13)

                ranxp = math.floor(ranpow+randen+ranhp /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'T','troll',colors.trollgreen,blocks=True,
                fighter=fighter_component, ai=ai_component)

            elif choice < 40+5+2: #2% chance
                #Create a gark
                ranhp = randint(2,4)
                randen = randint(2,3)
                ranpow = randint(2,6)
                ranxp = math.floor(ranpow+randen+ranhp /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'G','gark',colors.goblingreen, blocks=True,
                fighter=fighter_component, ai=ai_component)
            else:
                #Create a goblin
                ranhp = randint(2,60)
                randen = randint(0,1)
                ranpow = randint(1,4)
                ranxp = math.floor(ranpow+randen+ranhp /2)
                fighter_component = Fighter(hp=5, defense=1,power=ranpow,xpgain=ranxp,death_function=monster_death)
                ai_component = BasicMonster()

                monster = GameObject(x,y,'g','goblin',colors.goblingreen, blocks=True,
                fighter=fighter_component, ai=ai_component)


            objects.append(monster)

    num_items = randint(0, MAX_ROOM_ITEMS)

    for i in range(num_items):
        #choose random spot for this item
        x = randint(room.x1+1, room.x2-1)
        y = randint(room.y1+1, room.y2-1)

        #dont place on blocked tile
        if not is_blocked(x,y):
            #create a healing potion
            item_component = Item(use_function=cast_heal)
            item = GameObject(x, y, '!', 'healing potion', colors.violet,
                              item=item_component)

            #item = GameObject(x,y,'!','healing potion',colors.violet)

            objects.append(item)
            item.send_to_back() #items appear below other objects
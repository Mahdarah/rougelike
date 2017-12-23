class BasicMonster:
    #AI for a basic monster
    def take_turn(self):
        monster = self.owner
        if (monster.x, monster.y) in visible_tiles:

            if monster.distance_to(player) >=2:
                monster.move_towards(player.x,player.y)

            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
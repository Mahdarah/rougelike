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
            message(self.owner.name.capitalize() + ' attacks ' + target.name+ ' for '+str(damage), colors.lighter_han)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize()+ ' attacks ' + target.name+ ' but it had no effect')

    def heal(self,amount):
        #heal given amount without going over maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
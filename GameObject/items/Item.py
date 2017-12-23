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
            message('You picked up the ' + self.owner.name + '!', colors.green)

    def use(self):
        #call the use_function if defined
        if self.use_function is None:
            message('The '+self.owner.name+' cannot be used!')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner) #destroy after use, unless cancelled(e.g. trying to use health potion when health is full)
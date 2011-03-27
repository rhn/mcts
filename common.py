import time

from pymclevel import mclevel
import numpy

debug = True

def tacho(message, total, start):
    end = time.time()
    print message.format(total, end - start, int((end - start) / total))

def tacho_inv(message, total, start):
    end = time.time()
    print message.format(total, end - start, int(total / (end - start)))
    
    
class Point:
    def __init__(self, world, position, value):
        self.world_data = world
        self.position = position
        self.value = value
        self.visited = False # current generation. Neighbors to be verified this turn or already verified
        self.verified = False # neighbors verified

        if self.is_air():
            self.distance_from_wall = 2**16 - 1
        else:
            self.distance_from_wall = 0

    def __repr__(self):
        return 'P(' + str(self.position) + ', ' + str(self.distance_from_wall) + ')'
    
    __str__ = __repr__             


class Pixel(Point):
    def is_air(self):
        return self.value[1] != 0
    
    def mark_generation_number(self, generation_number):
        red, green, blue = self.value
        self.value = (generation_number % 256, green, blue)
        self.world_data[self.position] = self.value

    def mark_distance_from_wall(self):
        self.set_blue((self.distance_from_wall * 16) % 256)

    def mark_maximum(self):
        red, green, blue = self.value
        self.value = red, 0, 255
        self.world_data[self.position] = self.value

    def mark_final(self):
        self.value = (255, 0, 0)
        self.world_data[self.position] = self.value

    def set_red(self, value):
        red, green, blue = self.value
        self.world_data[self.position] = (value, green, blue)
        self.value = value, green, blue

    def set_blue(self, value):
        red, green, blue = self.value
        self.world_data[self.position] = (red, green, value)
        self.value = red, green, value
    
    def set_green(self, value):
        red, green, blue = self.value
        self.world_data[self.position] = (red, value, blue)
        self.value = red, value, blue

    def mark_removed(self):
        self.set_green(0)
        self.set_blue(0)


class Block(Point):
    # XXX: values sould be normal
    AIR_VALUES = [mclevel.materials.Air.ID]
    if debug:
        AIR_VALUES = [mclevel.materials.Cobblestone.ID] + [mclevel.materials.WoodPlanks.ID, mclevel.materials.Wood.ID, mclevel.materials.Sandstone.ID]
    VALUE = 1
    POSITION = 0
    VISITED = 2
    VERIFIED = 3
    DISTANCE_FROM_WALL = 4
    @classmethod
    def is_air(cls, point):
        return point[cls.VALUE] in cls.AIR_VALUES
    
    def set_material(self, material):
        x, y, z = self.position
        self.value = material.ID
        self.world_data.Blocks[x%16, y%16, z] = self.value
        self.world_data.modified = True
    
    @classmethod
    def mark_final(cls, block):
        block[cls.VISITED] = True
        block[cls.VALUE] = mclevel.materials.Brick.ID

    @classmethod
    def mark_maximum(cls, block):
        block[cls.VISITED] = True
        block[cls.VALUE] = mclevel.materials.Brick.ID

    def mark_distance_from_wall(self):
        return
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][self.distance_from_wall % 3])

    def mark_generation_number(self, generation):
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][generation % 3])
    
    @classmethod
    def mark_removed(cls, block):
        pass

    if debug:
        @classmethod
        def mark_removed(cls, block):
            block[cls.VISITED] = True
            block[cls.VALUE] = mclevel.materials.Glass.ID


ArrayBlock = numpy.dtype([('position', (numpy.int, 3)), # position
                          ('value', numpy.int), # value
                          ('visited', numpy.bool), # visited
                          ('verified', numpy.bool), # verified
                          ('distance_from_wall', numpy.int)]) # distance from wall


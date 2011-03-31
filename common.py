import time

from pymclevel import mclevel
import numpy


class PleaseSave(Exception):
    pass
    

class debug:
    small_area = True
    inverted_air = False

if debug.small_area:
    print 'Restricted area'

if debug.inverted_air:
    print 'Anti-air'


class Topic:
    def __init__(self):
        self.last_start = None
        self.last_result = None
        self.time_spent = None
        self.processed = 0
        self.normal_message = None
        self.inv_message = None

    def reset(self):
        self.last_start = time.time()

    def mark(self, processed):
        self.processed = self.processed + processed
        self.last_result = time.time()
        time_spent = self.last_result - self.last_start
        self.time_spent = self.time_spent + time_spent
        self.reset()
        return time_spent
    
    def print_message(self, processed, time_spent, total=False):
        time_per_object = int((time_spent) / processed)
        if time_per_object == 0:
            objects_per_second = int((processed) / time_spent)
            message = self.inv_message.format(processed, time_spent, objects_per_second)
        else:
            message = self.normal_message.format(processed, time_spent, time_per_object)
        if not total:
            message = '\t' + message
        print message

class TimingOutputter:
    def __init__(self):
        self.topics = {}
        
    def open(self, topic_name, normal_message, inv_message):
        topic = Topic()
        topic.time_spent = 0
        topic.normal_message = normal_message
        topic.inv_message = inv_message
        self.topics[topic_name] = topic
        self.reset(topic_name)
    
    def mark(self, topic_name, processed, silent=False):
        topic = self.topics[topic_name]
        time_spent = topic.mark(processed)
        if not silent:
            topic.print_message(processed, time_spent)
    
    def reset(self, topic_name):
        self.topics[topic_name].reset()
        
    def close(self, topic_name):
        topic = self.topics[topic_name]
        time_spent = topic.time_spent
        del self.topics[topic_name]
        topic.print_message(topic.processed, time_spent, total=True)


tacho = TimingOutputter()
    
    
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
    AIR_VALUES = (mclevel.materials.Air.ID, mclevel.materials.Torch.ID)
    if debug.inverted_air:
        AIR_VALUES = (mclevel.materials.Cobblestone.ID, mclevel.materials.WoodPlanks.ID, mclevel.materials.Wood.ID, mclevel.materials.Sandstone.ID)
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
        block[cls.VALUE] = mclevel.materials.LapisLazuliBlock.ID

    def mark_distance_from_wall(self):
        return
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][self.distance_from_wall % 3])

    def mark_generation_number(self, generation):
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][generation % 3])
    
    @classmethod
    def mark_removed(cls, block):
        pass

    if debug.inverted_air:
        @classmethod
        def mark_removed(cls, block):
            block[cls.VISITED] = True
            block[cls.VALUE] = mclevel.materials.Glass.ID


ArrayBlock = numpy.dtype([('position', (numpy.int, 3)), # position
                          ('value', numpy.int), # value
                          ('visited', numpy.bool), # visited
                          ('verified', numpy.bool), # verified
                          ('distance_from_wall', numpy.int)]) # distance from wall


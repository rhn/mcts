#!/usr/bin/python

import Image
import sys

import flood_fill

class Point:
    def __init__(self, world, position, value):
        self.world = world
        self.position = position
        self.value = value
        self.visited = False

        if self.is_air():
            self.distance_from_wall = 2**16 - 1
            self.distance_verified = False
        else:
            self.distance_from_wall = 0
            self.distance_verified = True


class Pixel(Point):
    def is_air(self):
        return self.value[1] != 0
    
    def mark_generation_number(self, generation_number):
        red, green, blue = self.value
        self.world.world_data[self.position] = generation_number % 256, green, blue

    def mark_distance_from_wall(self):
        self.set_blue((self.distance_from_wall * 16) % 256)

    def set_blue(self, value):
        red, green, blue = self.value
        self.world.world_data[self.position] = red, green, value
        self.value = red, green, value
    
    def set_green(self, value):
        red, green, blue = self.value
        self.world.world_data[self.position] = red, value, blue
        self.value = red, value, blue

    def __repr__(self):
        return 'P(' + str(self.position) + ', ' + str(self.distance_from_wall) + ')'
    
    __str__ = __repr__             


if __name__ == '__main__':
    world = Image.open(sys.argv[1])

    flood_filler = flood_fill.ImageFloodFill(world)
    if len(sys.argv) == 4:
        xpos = int(sys.argv[2])
        ypos = int(sys.argv[3])
        xsize, ysize = world.size
        
        if xsize <= xpos or ysize <= ypos:
            raise ValueError("Position exceeds size")
        
        starting_layer = [flood_filler.get_point((xpos, ypos))]
    else:
        starting_layer = []
        xsize, ysize = world.size
        for y in range(ysize):
            starting_layer.append(flood_filler.get_point((0, y)))

    flood_filler.flood_fill(starting_layer)    
    world.save('flood_fill.png')

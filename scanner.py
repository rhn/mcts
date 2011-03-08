#!/usr/bin/python

import Image
import sys


class Point:
    def __init__(self, world, position, value):
        self.world = world
        self.position = position
        self.value = value
        self.visited = False
        if self.is_air():
            self.distance_from_wall = 2**16
        else:
            self.distance_from_wall = 0


class Pixel(Point):
    def is_air(self):
        return self.value[1] != 0
    
    def mark_generation_number(self, generation_number):
        red, green, blue = self.value
        self.world.world_data[self.position] = generation_number % 256, green, blue

    def mark_distance_from_wall(self):
        red, green, blue = self.value
        self.world.world_data[self.position] = red, green, self.distance_from_wall % 256

    def __repr__(self):
        return str(self.position)

class FloodFill:
    def expand(self, layer):
        new_layer = set()
        for point in layer:
            for neighbor in self.get_neighbors(point):
                if neighbor.is_air():
                    if not neighbor.visited:
                        new_layer.add(neighbor)
            point.visited = True
        return new_layer
    
    def flood_fill(self, starting_position):
        layer = [self.get_point(starting_position)]
        i = 0
        while layer:
            i += 1
            layer = self.expand(layer)
            self.mark_generation(layer, i)   


class ImageFloodFill(FloodFill):
    def __init__(self, image):
        self.minx = 0
        self.miny = 0
        self.maxx, self.maxy = image.size
        self.world_data = image.load()
        self.image = image
        self.points = {}
    
    def get_point(self, position):
        if position not in self.points:
            self.points[position] = Pixel(self, position, self.world_data[position])
        return self.points[position]
        
    def mark_generation(self, layer, generation_number):
        for point in layer:
            point.mark_generation_number(generation_number)
            
        if generation_number % 20 == 0:
            self.image.save(str(generation_number) + '.png')
            print 'generation {0}, points on the edge: {1}'.format(generation_number, len(layer))
            #raw_input()
        
    def get_neighbors(self, point):
        xpos, ypos = point.position
        points = []
        for x, y in [                 (xpos, ypos - 1),
                     (xpos - 1, ypos),                 (xpos + 1, ypos),
                                      (xpos, ypos + 1),                 ]:
            if self.minx <= x < self.maxx and self.miny <= y < self.maxy:
                points.append(self.get_point((x, y)))
        return points
            
             


if __name__ == '__main__':
    world = Image.open(sys.argv[1])
    xpos = int(sys.argv[2])
    ypos = int(sys.argv[3])
    xsize, ysize = world.size
    
    if xsize <= xpos or ysize <= ypos:
        raise ValueError("Position exceeds size")
    
    flood_fill = ImageFloodFill(world)
    flood_fill.flood_fill((xpos, ypos))
    
    world.save('flood_fill.png')

#!/usr/bin/python

import Image
import sys

import flood_fill
import thinning


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
    
    thinner = thinning.ImageDistanceThinner(flood_filler.points)
    
    world.save('thinned.png')

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
        for x in range(xsize):
            starting_layer.append(flood_filler.get_point((x, 0)))

    flood_filler.flood_fill(starting_layer)    
    world.save('flood_fill.png')
    
    if True:
        try:
            world2 = world.copy()
            world_data2 = world2.load()
            new_points = {}
            for position, point in flood_filler.points.items():
                new_point = flood_fill.Pixel(world_data2, position, point.value)
                new_point.distance_from_wall = point.distance_from_wall
                new_points[position] = new_point
            reload(thinning)
            thinner = thinning.ImageDistanceThinner(new_points)
            thinner.image = world2
            thinner.perform_thinning()
            world2.save('thinned.png')
        except KeyboardInterrupt:
            print 'interrupted'
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            print 'broken'
        print 'finished'
      #  raw_input()

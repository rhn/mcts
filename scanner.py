#!/usr/bin/python

from pymclevel import mclevel
import sys

import flood_fill
import thinning
import graph

def copy_data(world, points):
    world2 = world.copy()
    world_data2 = world2.load()
    new_points = {}
    for position, point in points.items():
        new_point = flood_fill.Pixel(world_data2, position, point.value)
        new_point.distance_from_wall = point.distance_from_wall
        new_points[position] = new_point
    return world2, new_points
    

if __name__ == '__main__':
    world = mclevel.fromFile(sys.argv[1])

    flood_filler = flood_fill.MCFloodFill(world)
    layer = flood_filler.get_starting_layer()
    print 'layer contains', len(layer), 'blocks'
    print len([point for point in layer if point.is_air()])
    flood_filler.flood_fill(layer)    
    print 'changing'
    for chunk in (world.getChunk(cx, cy) for cx, cy in world.allChunks):
        chunk.chunkChanged()
    print 'lighting'
    world.generateLights()
    print 'saving'
    world.saveInPlace()
    print 'duping'
    raise NotImplementedException
    thinner = thinning.ImageDistanceThinner(flood_filler.points)
    thinner.image = world
    thinner.perform_thinning()
    world.save('thinned.png')
    
    while True:
        try:
            reload(graph.backend)
            reload(graph)
            print 'copying'
            world2, points2 = copy_data(world, thinner.points)
            print 'done copying'
            grapher = graph.Grapher(points2)
            grapher.make_graph()
            world2.save('graphed.png')
            print 'finished'
        except KeyboardInterrupt:
            print 'interrupted'
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            print 'broken'
        raw_input()

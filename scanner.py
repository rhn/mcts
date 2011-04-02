#!/usr/bin/python

import sys
from pymclevel import mclevel

import flood_fill
import thinning
import graph
import common

def copy_data(world, points):
    world2 = world.copy()
    world_data2 = world2.load()
    new_points = {}
    for position, point in points.items():
        new_point = flood_fill.Pixel(world_data2, position, point.value)
        new_point.distance_from_wall = point.distance_from_wall
        new_points[position] = new_point
    return world2, new_points


def save(world):
    print 'changing'
    for chunk in (world.getChunk(cx, cy) for cx, cy in world.allChunks):
        if hasattr(chunk, 'modified') and chunk.modified == True:
            chunk.chunkChanged()
    print 'lighting'
    world.generateLights()
    print 'saving'
    world.saveInPlace()

if __name__ == '__main__':
    import time
    world = mclevel.fromFile(sys.argv[-1])
    print 'air blocks:', common.Block.AIR_VALUES
    flood_filler = flood_fill.MCFloodFill(world)

    if len(sys.argv) > 2: # old engine
        layer = flood_filler.get_starting_layer()
        print 'layer contains', len(layer), 'blocks'
        flood_filler.flood_fill(layer)
        print 'flood filling done'
        thinner = thinning.MCDistanceThinner(flood_filler.chunks)
        thinner.image = world
        thinner.perform_thinning()
    else:
        try:
            thinner = flood_filler.dilate()
        except common.PleaseSave:
            print 'save requested'

    while True:
        try:
            reload(graph.backend)
            reload(graph)
            grapher = graph.MCGrapher(thinner.unremoved)
            grapher.make_graph()
            
            print 'updating'
            flood_filler.update_world()
            print 'saving'
            save(world)
            print 'finished'
        except KeyboardInterrupt:
            print 'interrupted'
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            print 'broken'
        raw_input()

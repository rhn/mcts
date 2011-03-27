#!/usr/bin/python

from pymclevel import mclevel
import sys

import flood_fill
import thinning
import graph

def tacho_inv(message, total, start):
    end = time.time()
    print message.format(total, end - start, int(total / (end - start)))

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
            print chunk
            chunk.chunkChanged()
    print 'lighting'
    world.generateLights()
    print 'saving'
    world.saveInPlace()

if __name__ == '__main__':
    import time
    world = mclevel.fromFile(sys.argv[1])
    print 'air blocks:', flood_fill.Block.AIR_VALUES
    flood_filler = flood_fill.MCFloodFill(world)
    start = time.time()
    layer = flood_filler.get_starting_layer()
    tacho('Processed {0} chunks in {1}s, {2}s per chunk', len(flood_filler.chunks), start)
    print 'layer contains', len(layer), 'blocks'
    flood_filler.flood_fill(layer)    
    print 'flood filling done'
    thinner = thinning.MCDistanceThinner(flood_filler.chunks)
    thinner.image = world
    thinner.perform_thinning()
    print 'updating'
    flood_filler.update_world()
    print 'saving'
    save(world)
    raise NotImplementedError
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

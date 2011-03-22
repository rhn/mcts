import time
from pymclevel import mclevel
import numpy
import itertools

def tacho(message, total, start):
    end = time.time()
    print message.format(total, end - start, int((end - start) / total))


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
#    AIR_VALUES = [mclevel.materials.Air.ID]
    AIR_VALUES = [mclevel.materials.Cobblestone.ID] + [mclevel.materials.WoodPlanks.ID, mclevel.materials.Wood.ID, mclevel.materials.Sandstone.ID]
    VALUE = 1
    POSITION = 0
    VISITED = 2
    VERIFIED = 3
    DISTANCE_FROM_WALL = 4
    @staticmethod
    def is_air(block):
        return block.value in AIR_VALUES
    
    def set_material(self, material):
        x, y, z = self.position
        self.value = material.ID
        self.world_data.Blocks[x%16, y%16, z] = self.value
        self.world_data.modified = True
    
    def mark_final(self):
        self.set_material(mclevel.materials.Brick)

    def mark_maximum(self):
        self.set_material(mclevel.materials.LapisLazuliBlock)

    def mark_distance_from_wall(self):
        return
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][self.distance_from_wall % 3])

    def mark_generation_number(self, generation):
        self.set_material([mclevel.materials.WoodPlanks, mclevel.materials.Wood, mclevel.materials.Sandstone][generation % 3])
    
    def mark_removed(self):
        self.set_material(mclevel.materials.Glass)


ArrayBlock = numpy.dtype([('position', (numpy.int, 3)), # position
                          ('value', numpy.int), # value
                          ('visited', numpy.bool), # visited
                          ('verified', numpy.bool), # verified
                          ('distance_from_wall', numpy.int)]) # distance from wall


class FloodFill:
    def expand_distances(self, layer):
        new_layer = set()
        
        if layer:
            dist = list(layer)[0][Block.DISTANCE_FROM_WALL]
        
#        print 'dist', dist
        
        for point in layer:
            if point[Block.DISTANCE_FROM_WALL] != dist:
                print layer
                print point, dist
                raise Exception('point borked')
#            print point, self.get_neighbors(point)
            for neighbor in self.get_neighbors(point):
                if self.is_air(neighbor) and neighbor[Block.VISITED] and neighbor[Block.DISTANCE_FROM_WALL] > point[Block.DISTANCE_FROM_WALL] + 1:
                    neighbor[Block.DISTANCE_FROM_WALL] = point[Block.DISTANCE_FROM_WALL] + 1
                    new_layer.add(neighbor)
        return new_layer

    def update_distances(self, layer):
        start = len(layer)
        c = 0
        distance = 1

        while layer:
            distance += 1
            layer = self.expand_distances(layer)
            c += len(layer)
            self.mark_distance_from_wall(layer) # TODO: slows down everything, called many times for the same pixels
        if c > 0:
            print '\tbefore distance {0}, points processed: {1} updated: {2}'.format(distance, start, c)
           # raw_input()

    def expand(self, layer):
        near_walls = []
        new_layer = []
        '''
        print 'starting with'
        print layer
        '''
        for point in layer:
            point[Block.VISITED] = True
        
        for point in layer:
            possible_wall_distances = [point[Block.DISTANCE_FROM_WALL]]
            for neighbor in self.get_neighbors(point):
                if self.is_air(neighbor):
                    if not neighbor[Block.VISITED]:
                      try:
                        found = False
                        for element in new_layer: # hack workaround The truth value of an array with more than one element is ambiguous.
                            if (element == neighbor).all():
                                found = True
                        if not found:
                            new_layer.append(neighbor)
                      except Exception, e:
                        import traceback
                        traceback.print_exc(e)
                        print neighbor
                        print new_layer
                        raw_input()
                    if neighbor[Block.VERIFIED]:
                        possible_wall_distances.append(neighbor[Block.DISTANCE_FROM_WALL] + 1)
                else: # neighbor is wall
                    possible_wall_distances.append(1)
                    
            point[Block.DISTANCE_FROM_WALL] = min(possible_wall_distances)
            if point[Block.DISTANCE_FROM_WALL] == 1:
                near_walls.append(point)

        for point in layer: # distance was updated, point is not in the front line
            point[Block.VERIFIED] = True
        '''
        print 'updated distances'
        print layer    
        
        print 'detected walls'
        print walls_hit
        '''
        self.mark_distance_from_wall(layer) # TODO: slows down everything, called many times for the same pixels
        self.update_distances(near_walls)
        '''
        print 'new distances'
        print layer
        
        print new_layer
        raw_input()
        '''
        
        return new_layer
    
    def flood_fill(self, layer=None):
        if layer is None:
            layer = self.get_starting_layer()
        start = time.time()
        i = 0
        while layer:
            i += 1
            self.generation = i
            layer = self.expand(layer)
            self.mark_generation(layer, i)   
        tacho('Processed {0} layers in {1}s, {2}s per layer', i, start)

    def mark_generation(self, layer, generation_number):
        print 'generation {0}, points on the edge: {1}'.format(generation_number, len(layer))
        return
        for point in layer:
            point.mark_generation_number(generation_number)
            
    def mark_distance_from_wall(self, layer):
        return
        for point in layer:
            point.mark_distance_from_wall()


class MCFloodFill(FloodFill):
    CHUNK_SIZE = 16
    CHUNK_HEIGHT = 128
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def __init__(self, world):
        self.world = world
        self.chunks = {}
        self.chunk_coords = set(world.allChunks) # Chunks should never be added/removed, so this is allowed
        
    def get_starting_layer(self):
        layer = []
        for cx, cy in [(0, 0), (0, -1), (-1, 0), (-1, -1)]:
        #for cx, cy in self.world.allChunks:
            base_x = cx * self.CHUNK_SIZE
            base_y = cy * self.CHUNK_SIZE
            for x in range(base_x, base_x + self.CHUNK_SIZE):
                for y in range(base_y, base_y + self.CHUNK_SIZE):
                    point = self.get_point((x, y, self.CHUNK_HEIGHT - 1))
                    if self.is_air(point):
                        layer.append(point)
        return layer
    
    def get_point(self, position):
        x, y, z = position
        cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
        chunk = self.world.getChunk(cx, cy)
        if not (cx, cy) in self.chunks:
            extended_blocks = numpy.zeros((self.CHUNK_SIZE, self.CHUNK_SIZE, self.CHUNK_HEIGHT), ArrayBlock)
            self.chunks[cx, cy] = extended_blocks
            chunk.extended_blocks = extended_blocks
            blocks = chunk.Blocks
            offsetx, offsety = cx * self.CHUNK_SIZE, cy * self.CHUNK_SIZE
            for point_position in itertools.product(range(self.CHUNK_SIZE), range(self.CHUNK_SIZE), range(self.CHUNK_HEIGHT)):
                block = extended_blocks[point_position]
                block[Block.VALUE] = blocks[point_position]
                nx, ny, nz = point_position
                nx = nx + offsetx
                ny = ny + offsety
                block[Block.POSITION][:] = numpy.array((nx, ny, nz))
                block[Block.DISTANCE_FROM_WALL] = 65536
        else:
            extended_blocks = self.chunks[cx, cy]
        return extended_blocks[x % self.CHUNK_SIZE, y % self.CHUNK_SIZE, z]

    def contains(self, position):
        x, y, z = position
        return (x / self.CHUNK_SIZE, y / self.CHUNK_SIZE) in self.chunk_coords and 0 <= z < 128

    def get_neighbors(self, point):
        x, y, z = point[Block.POSITION]
        points = []
        for deltax, deltay, deltaz in self.NEIGHBORS:
            neighbor_position = (x + deltax, y + deltay, z + deltaz)
            if self.contains(neighbor_position):
                points.append(self.get_point(neighbor_position))
        return points
    
    def is_air(self, point):
        return point[Block.VALUE] in Block.AIR_VALUES
    

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
            self.points[position] = Pixel(self.world_data, position, self.world_data[position])
        return self.points[position]
                
    def get_neighbors(self, point):
        xpos, ypos = point.position
        points = []
        for x, y in [                 (xpos, ypos - 1),
                     (xpos - 1, ypos),                 (xpos + 1, ypos),
                                      (xpos, ypos + 1),                 ]:
            if self.minx <= x < self.maxx and self.miny <= y < self.maxy:
                points.append(self.get_point((x, y)))
        return points


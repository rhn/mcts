import time
import itertools
from common import *
import thinning
from pymclevel import mclevel


def dilate(layer, get_neighbors):
    new_layer = {}
    for point in layer:
        for neighbor in get_neighbors(point):
            new_layer[tuple(neighbor[Block.POSITION])] = neighbor
    return new_layer.values()
    

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
                if Block.is_air(neighbor) and neighbor[Block.VISITED] and neighbor[Block.DISTANCE_FROM_WALL] > point[Block.DISTANCE_FROM_WALL] + 1:
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
            if c > 0 and distance > 1:
                print '\tprocessing {0} points'.format(start)
            self.mark_distance_from_wall(layer) # TODO: slows down everything, called many times for the same pixels
        if c > 0:
            print '\tbefore distance {0} updated: {1} points'.format(distance, c)
           # raw_input()

    def expand(self, layer):
        near_walls = []
        new_layer = {}

        for point in layer:
            point[Block.VISITED] = True
        
        for point in layer:
            possible_wall_distances = [point[Block.DISTANCE_FROM_WALL]]
            for neighbor in self.get_neighbors(point):
                if Block.is_air(neighbor):
                    if not neighbor[Block.VISITED]:
                        position = tuple(neighbor[Block.POSITION])
                        new_layer[position] = neighbor
                    if neighbor[Block.VERIFIED]:
                        possible_wall_distances.append(neighbor[Block.DISTANCE_FROM_WALL] + 1)
                else: # neighbor is wall
                    possible_wall_distances.append(1)
                    
            point[Block.DISTANCE_FROM_WALL] = min(possible_wall_distances)
            if point[Block.DISTANCE_FROM_WALL] == 1:
                near_walls.append(point)

        for point in layer: # distance was updated, point is not in the front line
            point[Block.VERIFIED] = True

        self.update_distances(near_walls)

        return new_layer.values()
    
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


    def dilate(self):
        tacho.open('skeletization', 'Skeletization completed in {1}s.', 'Skeletization completed in {1}s.')
        layer = self.get_air_neighboring_walls()
        tacho.open('dilating', 'Dilated {0} points in {1}s, {2}s per point', 'Dilated {0} points in {1}s, {2} points per second')
        tacho.open('thinning', 'Thinned {0} points in {1}s, {2}s per point', 'Thinned {0} points in {1}s, {2} points per second')
        thinner = self.build_thinner()
        
        def get_neighbors(point):
            return (neighbor for neighbor in self.get_neighbors(point) if not neighbor[Block.VISITED])
        
        distance = 1
        while layer:
            points = len(layer)
        #    self.mark_generation(layer, distance)            
            print 'distance', distance

            for point in layer:
                point[Block.VISITED] = True
                point[Block.DISTANCE_FROM_WALL] = distance
                
            thinner.thin_layer(layer)

            tacho.reset('dilating')

            layer = dilate(layer, get_neighbors)
            distance += 1
            
            tacho.mark('dilating', points)
        
        tacho.mark('skeletization', 1, silent=True)
        tacho.close('dilating')
        tacho.close('thinning')
        
        print 'Thinning finished with {0} points left.'.format(len(thinner.unremoved))
        tacho.close('skeletization')
        
        thinner.check()
        
        
        for point in thinner.unremoved:
            Block.mark_final(point)
        
        for point in thinner.peaks:
            Block.mark_maximum(point)
        
        return thinner

    def mark_generation(self, layer, generation_number):
        print 'generation {0}, points on the edge: {1}'.format(generation_number, len(layer))
        for point in layer:
            point.mark_generation_number(generation_number)


class MCFloodFill(FloodFill):
    CHUNK_SIZE = 16
    CHUNK_HEIGHT = 128
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def __init__(self, world):
        self.world = world
        self.chunks = {}
        self.chunk_coords = set(world.allChunks) # Chunks should never be added/removed, so this is allowed 
        if debug.small_area:
            self.chunk_coords = debug.selected_chunks
        
    def get_starting_layer(self):
        chunks = self.world.allChunks
        if debug.small_area:
            chunks = debug.selected_chunks
    
        layer = []
        for cx, cy in chunks:
            base_x = cx * self.CHUNK_SIZE
            base_y = cy * self.CHUNK_SIZE
            for x in range(base_x, base_x + self.CHUNK_SIZE):
                for y in range(base_y, base_y + self.CHUNK_SIZE):
                    point = self.get_point((x, y, self.CHUNK_HEIGHT - 1))
                    if Block.is_air(point):
                        layer.append(point)
        return layer
    
    def get_air_neighboring_walls(self):
        chunks = [chunk for chunk in self.world.allChunks]
        if debug.small_area:
            chunks = debug.selected_chunks
        
        layer = []
        
        print 'loading', len(chunks), 'chunks'
        tacho.open('loading', 'Loaded {0} chunks in {1}s, {2}s per chunk', 'Loaded {0} chunks in {1}s, {2} chunks per second')
        
        for i, (cx, cy) in enumerate(chunks):
            if not (cx, cy) in self.chunks:
                try:
                    self._load_chunk(cx, cy)
                except mclevel.ChunkNotPresent:
                    continue
            extended_blocks = self.chunks[cx, cy].extended_blocks
            for point in extended_blocks.flat:
                if point[Block.VALUE] in Block.AIR_VALUES:
                    for neighbor in self.get_neighbors(point):
                        if neighbor[Block.VALUE] not in Block.AIR_VALUES:
                            layer.append(point)
                            break
                else:
                    point[Block.VISITED] = True
                    point[Block.DISTANCE_FROM_WALL] = 0
            tacho.mark('loading', 1)
        tacho.close('loading')
        return layer
    
    def _load_chunk(self, cx, cy):
        chunk = self.world.getChunk(cx, cy)
        extended_blocks = numpy.zeros((self.CHUNK_SIZE, self.CHUNK_SIZE, self.CHUNK_HEIGHT), ArrayBlock)
        self.chunks[cx, cy] = chunk
        chunk.extended_blocks = extended_blocks
        blocks = chunk.Blocks
        offsetx, offsety = cx * self.CHUNK_SIZE, cy * self.CHUNK_SIZE
        for point_position in itertools.product(range(self.CHUNK_SIZE), range(self.CHUNK_SIZE), range(self.CHUNK_HEIGHT)):
            block = extended_blocks[point_position]
            value = blocks[point_position]
            if debug.remove_air and value in Block.AIR_VALUES:
                value = 0
            block[Block.VALUE] = value
            x, y, z = point_position
            x = x + offsetx
            y = y + offsety
            block[Block.POSITION][:] = numpy.array((x, y, z))
            block[Block.DISTANCE_FROM_WALL] = 65535
    
    def get_point(self, position):
        x, y, z = position
        cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
        try:
            chunk = self.chunks[cx, cy]
        except KeyError:
            self._load_chunk(cx, cy)
            chunk = self.chunks[cx, cy]
        extended_blocks = chunk.extended_blocks
        return extended_blocks[x % self.CHUNK_SIZE, y % self.CHUNK_SIZE, z]

    def contains(self, position):
        x, y, z = position
        return (x / self.CHUNK_SIZE, y / self.CHUNK_SIZE) in self.chunk_coords and 0 <= z < self.CHUNK_HEIGHT

    def get_neighbors(self, point): # make use of chunks if point not on chunk edge
        x, y, z = point[Block.POSITION]
        adjx = x % self.CHUNK_SIZE
        adjy = y % self.CHUNK_SIZE

        points = []        
        #if True:
        if (not adjx) or (not adjy) or (not z) or adjx + 1 == self.CHUNK_SIZE or adjy + 1 == self.CHUNK_SIZE or z + 1 == self.CHUNK_HEIGHT: # on chunk_edge
            # use normal technique
            for deltax, deltay, deltaz in self.NEIGHBORS:
                neighbor_position = (x + deltax, y + deltay, z + deltaz)
                if self.contains(neighbor_position):
                    points.append(self.get_point(neighbor_position))
        else: # inside chunk
            # all points present
            cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
            extended_blocks = self.chunks[cx, cy].extended_blocks
            for deltax, deltay, deltaz in self.NEIGHBORS:
                neighbor_chunk_position = (adjx + deltax, adjy + deltay, z + deltaz) 
                points.append(extended_blocks[neighbor_chunk_position])
        return points

    def update_world(self):
        tacho.open('updating', 'Updated {0} chunks in {1}s, {2}s per chunk', 'Updated {0} chunks in {1}s, {2} chunks per second')
        for (cx, cy), chunk in self.chunks.items():
            extended_blocks = chunk.extended_blocks
            blocks = chunk.Blocks
            for block in extended_blocks.flat:
                if block[Block.VISITED]:
                    x, y, z = block[Block.POSITION]
                    blocks[x % self.CHUNK_SIZE, y % self.CHUNK_SIZE, z] = block[Block.VALUE]
                    chunk.modified = True
            tacho.mark('updating', 1)
        tacho.close('updating')
        
    def build_thinner(self):
        return thinning.MCDistanceThinner(self.chunks)

class ImageFloodFill(FloodFill):
    def __init__(self, image):
        self.minx = 0
        self.miny = 0
        self.maxx, self.maxy = image.size
        self.world_data = image.load()
        self.image = image
        self.points = {}
    
    def get_points(self):
        for x in range(self.minx, self.maxx):
            for y in range(self.miny, self.maxy):
                yield self.get_point((x, y))
    
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


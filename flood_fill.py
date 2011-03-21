from pymclevel import mclevel

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
    # AIR_VALUES = [mclevel.materials.Air.ID]
    AIR_VALUES = [mclevel.materials.Cobblestone.ID] + [mclevel.materials.WoodPlanks.ID, mclevel.materials.Wood.ID, mclevel.materials.Sandstone.ID]
    def is_air(self):
        return self.value in self.AIR_VALUES
    
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


class FloodFill:
    def expand_distances(self, layer):
        new_layer = set()
        
        if layer:
            dist = list(layer)[0].distance_from_wall
        
#        print 'dist', dist
        
        for point in layer:
            if point.distance_from_wall != dist:
                print layer
                print point, dist
                raise Exception('point borked')
#            print point, self.get_neighbors(point)
            for neighbor in self.get_neighbors(point):
                if neighbor.is_air() and neighbor.visited and neighbor.distance_from_wall > point.distance_from_wall + 1:
                    neighbor.distance_from_wall = point.distance_from_wall + 1
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
        new_layer = set()
        '''
        print 'starting with'
        print layer
        '''
        for point in layer:
            point.visited = True
        
        for point in layer:
            possible_wall_distances = [point.distance_from_wall]
            for neighbor in self.get_neighbors(point):
                if neighbor.is_air():
                    if not neighbor.visited:
                        new_layer.add(neighbor)
                    if neighbor.verified:
                        possible_wall_distances.append(neighbor.distance_from_wall + 1)
                else: # neighbor is wall
                    possible_wall_distances.append(1)
                    
            point.distance_from_wall = min(possible_wall_distances)
            if point.distance_from_wall == 1:
                near_walls.append(point)

        for point in layer: # distance was updated, point is not in the front line
            point.verified = True
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
        raw_input()
        '''
        return new_layer
    
    def flood_fill(self, layer=None):
        if layer is None:
            layer = self.get_starting_layer()
        i = 0
        while layer:
            i += 1
            self.generation = i
            layer = self.expand(layer)
            self.mark_generation(layer, i)   

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
        self.points = {}
        self.chunk_coords = set(world.allChunks) # Chunks should never be added/removed, so this is allowed
        
    def get_starting_layer(self):
        layer = []
        for cx, cy in self.world.allChunks:
            base_x = cx * self.CHUNK_SIZE
            base_y = cy * self.CHUNK_SIZE
            for x in range(base_x, base_x + self.CHUNK_SIZE):
                for y in range(base_y, base_y + self.CHUNK_SIZE):
                    point = self.get_point((x, y, self.CHUNK_HEIGHT - 1))
                    if point.is_air():
                        layer.append(point)
        return layer
    
    def get_point(self, position):
        if position not in self.points:
            x, y, z = position
            cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
            chunk = self.world.getChunk(cx, cy)
            self.points[position] = Block(chunk, position, chunk.Blocks[x % self.CHUNK_SIZE, y % self.CHUNK_SIZE, z])
        return self.points[position]

    def contains(self, position):
        x, y, z = position
        return (x / self.CHUNK_SIZE, y / self.CHUNK_SIZE) in self.chunk_coords and 0 <= z < 128

    def get_neighbors(self, point):
        x, y, z = point.position
        points = []
        for deltax, deltay, deltaz in self.NEIGHBORS:
            neighbor_position = (x + deltax, y + deltay, z + deltaz)
            if self.contains(neighbor_position):
                points.append(self.get_point(neighbor_position))
        return points
        

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


class FloodFill:
    def expand_distances(self, layer):
        new_layer = set()
        
        if layer:
            dist = list(layer)[0].distance_from_wall
        
        for point in layer:
            if point.distance_from_wall != dist:
                raise Exception('point borked')
            for neighbor in self.get_neighbors(point):
                if neighbor.is_air() and neighbor.visited and neighbor.distance_from_wall > point.distance_from_wall + 1:
                    neighbor.distance_from_wall = point.distance_from_wall + 1
                    new_layer.add(neighbor)
        return new_layer

    def update_distances(self, layer):
        c = len(layer)
        distance = 1

        while layer:
            distance += 1
            layer = self.expand_distances(layer)
            c += len(layer)
            self.mark_distance_from_wall(layer) # TODO: slows down everything, called many times for the same pixels
            '''
            for point in layer:
                point.set_green(127)
            self.image.save('dist-' + str(distance) + '.png')
            for point in layer:
                point.set_green(255)
            #print '\tdistance {0}, points on the edge: {1}'.format(distance, len(layer))
        '''
        if c > 0:
            print '\tdistance {0}, points processed: {1}'.format(distance, c)
           # raw_input()

    def expand(self, layer):
        hit_wall = set()
        new_layer = set()
        
        for point in layer:
            possible_wall_distances = [point.distance_from_wall]
            for neighbor in self.get_neighbors(point):
                if neighbor.distance_verified:
                    possible_wall_distances.append(neighbor.distance_from_wall + 1)
                if neighbor.is_air():
                    if not neighbor.visited:
                        new_layer.add(neighbor)
                else: # neighbor is wall
                    hit_wall.add(point)

                    
            point.distance_from_wall = min(possible_wall_distances)
            point.visited = True
            
        self.mark_distance_from_wall(layer) # TODO: slows down everything, called many times for the same pixels
        self.update_distances(hit_wall)
        
        for point in layer:
            point.distance_verified = True

        return new_layer
    
    def flood_fill(self, layer):
        i = 0
        while layer:
            i += 1
            self.generation = i
            layer = self.expand(layer)
            self.mark_generation(layer, i)   

    def mark_generation(self, layer, generation_number):
        for point in layer:
            point.mark_generation_number(generation_number)
        if generation_number % 10 == 0:
            self.image.save(str(generation_number) + '.png')
            
        print 'generation {0}, points on the edge: {1}'.format(generation_number, len(layer))
            #raw_input()
            
    def mark_distance_from_wall(self, layer):
        for point in layer:
            point.mark_distance_from_wall()


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
                
    def get_neighbors(self, point):
        xpos, ypos = point.position
        points = []
        for x, y in [                 (xpos, ypos - 1),
                     (xpos - 1, ypos),                 (xpos + 1, ypos),
                                      (xpos, ypos + 1),                 ]:
            if self.minx <= x < self.maxx and self.miny <= y < self.maxy:
                points.append(self.get_point((x, y)))
        return points


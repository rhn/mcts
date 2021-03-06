from common import Block, tacho


class DistanceThinner:
    def __init__(self):
        self.unremoved = []
        self.peaks = []
        
    def is_local_peak(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor[Block.DISTANCE_FROM_WALL] >= point[Block.DISTANCE_FROM_WALL]:
                return False
        return True
    
    def is_local_maximum(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor.distance_from_wall > point.distance_from_wall:
                return False
        return True

    def get_points(self, positions):
        raise NotImplementedError
    
    def get_positions(self, points):
        positions = []
        for point in points:
            positions.append(tuple(point[Block.POSITION]))
        return positions
        
    def thin_layer(self, layer):
        peaks = self.peaks
        unremoved = self.unremoved
        
        tacho.reset('thinning')
        
        processed_points = unremoved + layer
        
        total = len(processed_points)
        print '\tThinning - points on the edge {0}, previously untouched {1},\n' \
              '\t\t---- total {2}'.format(len(layer), len(unremoved), total)
        
        modified_neighbors = layer
#        modified_neighbors = processed_points

        deleted = 0
        i = 0

        while modified_neighbors:
            i += 1
            #iterdel = 0
            new_modified_neighbors = []
            #print len(modified_neighbors), len(set(self.get_positions(modified_neighbors)))
            for point in modified_neighbors:
                # if deleted or not flooded or wall
                if point[Block.VERIFIED] or not point[Block.VISITED] or point[Block.VALUE] not in Block.AIR_VALUES:
                    #print 'pass', point
                    continue
                    '''
                print point
'''
                neighbors = self.get_neighbors(point)
                neighbors = filter(self.unremoved_point, neighbors)                
                if self.is_local_peak(point, neighbors):
                    peaks.append(point)
                else:

                    if self.is_expendable(point, neighbors):
                        self.remove_point(point) # deletion must be immediate. otherwise two neighboring maxima would both either stay or erase
                        modified = True
                        deleted += 1
                        new_modified_neighbors.extend(neighbors)
                        '''
                        print point
                        print neighbors
                        print [point for point in neighbors if not point[Block.VERIFIED] and point[Block.VISITED]]
                        raw_input()'''
                    else: # point is not maximum but had to stay
                        pass
                '''
                print point
                raw_input()
                '''
            modified_neighbors = new_modified_neighbors
       
        '''
        for point in processed_points:
            if not point[Block.VERIFIED]:
                neighbors = self.get_neighbors(point)
                if not self.is_local_peak(point, neighbors):
                    if self.is_expendable(point, neighbors):
                        raise Exception("fail")
        '''     
        
        unremoved = [point for point in processed_points if not point[Block.VERIFIED]]
        
        '''       
        for point in unremoved:
            if not point[Block.VERIFIED]:
                neighbors = self.get_neighbors(point)
                if not self.is_local_peak(point, neighbors):
                    if self.is_expendable(point, neighbors):
                        raise Exception("fail2")
           '''  
        
        self.unremoved = unremoved
        self.peaks = peaks
        
        tacho.mark('thinning', total)
        
        print '\tThinning removed {0} points in {1} iterations, left {2}'.format(deleted, i, len(unremoved))
    

class ProgressiveDistanceThinner(DistanceThinner):
    def __init__(self, points):
        self.points = points
        DistanceThinner.__init__(self)
    
    def get_sorted_points(self): # can be optimized
        distances = {}
        for position, point in self.points.items():
            distance = point[Block.DISTANCE_FROM_WALL]
            if distance not in distances:
                distances[distance] = set()
            distances[distance].add(point)
        return distances

    def get_points(self, positions):
        points = []
        for position in positions:
            points.append(self.points[position])
        return points

    def remove_point(self, point):
        del self.points[tuple(point[Block.POSITION])]

    def perform_thinning(self):
        print
        print 'sorting {0} points into layers'.format(len(self.points))
        
        distances = self.get_sorted_points()
        
        if 0 in distances: # there are walls in it
            for point in distances[0]:
                del self.points[tuple(point[Block.POSITION])]
            del distances[0]
        
        total_points = len(self.points)
        
        print 'thinning {0} points'.format(total_points)
        print
        
        for distance in sorted(distances.keys()):
            layer = distances[distance]
            self.thin_layer(layer)
                #self.image.save('thin-' + str(distance) + '.png')
            #raw_input()
        for position in self.unremoved:
            Block.mark_final(self.points[position])
        
        print 'Thinning finished with {0} points left out of {1}'.format(len(self.unremoved), total_points)


def dim3_connected4_expendable(self, point, neighbors):
    if len(neighbors) == 0:
        return False
        raise Exception("no neighbors! can't happen, the code is too stupid to allow these situations, let alone handle them " + str(point) + ' ' + str(self.get_neighbors(point)))
    
    if len(neighbors) == 1:
        return True
    
    if len(neighbors) == 2: # Two possibilities: corner or connection
        posx0, posy0, posz0 = neighbors[0][Block.POSITION]
        posx1, posy1, posz1 = neighbors[1][Block.POSITION]
        
        if abs(posx0 - posx1) == 2 or abs(posy0 - posy1) == 2 or abs(posz0 - posz1) == 2: # if neighbors opposite to each other, i.e. distances differ by 2
            return False # connection inside a line
        
        # Point lies on a corner: now check if removal causes disconnections.
        # There will be no disconections if there exists another point neighboring both neighbors.
        # Because thinning works from lowest to highest distance, that point will never be closer to wall
        posx, posy, posz = point[Block.POSITION]
        insider_position = (posx0 - (posx - posx1), posy0 - (posy - posy1), posz0 - (posz - posz1)) # TODO: check if valid
        if self.unremoved_position(insider_position): # there is another point connecting the same way
            return True # feel free to remove me     
        else:
            return False
    
    elif len(neighbors) == 3: # 2 options: either corner or flat
        #posx, posy, posz = point.position
        posx0, posy0, posz0 = neighbors[0][Block.POSITION]
        posx1, posy1, posz1 = neighbors[1][Block.POSITION]
        posx2, posy2, posz2 = neighbors[2][Block.POSITION]
        
        maxx, minx = max(posx0, posx1, posx2), min(posx0, posx1, posx2)
        maxy, miny = max(posy0, posy1, posy2), min(posy0, posy1, posy2)
        maxz, minz = max(posz0, posz1, posz2), min(posz0, posz1, posz2)
        
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                for z in range(minz, maxz + 1):
                    if not self.unremoved_position((x, y, z)):
                        return False # this point looks like a connector
        return True # this point is a part of a solid block of 6 (if flat) or 4 (if 3D)
   
    elif len(neighbors) == 6:
        return False
    
    else:
        # 5 or 4

        positions = zip(*(neighbor[Block.POSITION] for neighbor in neighbors))
        maxima, minima = map(max, positions), map(min, positions)
        if len(neighbors) == 4: # 2 options: cross or part of block
            sizes = [maximum - minimum for maximum, minimum in zip(maxima, minima)]
            if 0 in sizes: # cross connection. removal will make a hole
                return False
            
        for x in range(minima[0], maxima[0] + 1):
            for y in range(minima[1], maxima[1] + 1):
                for z in range(minima[2], maxima[2] + 1):
                    if not self.unremoved_position((x, y, z)):
                        return False # this point looks like a connector
        return True # this point is a part of a solid block and is exposed on one side
    return False # unknown case...
    

class MCDistanceThinner(DistanceThinner):
    CHUNK_SIZE = 16
    CHUNK_HEIGHT = 128
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def __init__(self, chunks):
        """chunks is {(cx, cy): chunk}"""
        self.chunks = chunks
        DistanceThinner.__init__(self)
    
    def get_points(self, positions):
        points = []
        for position in positions:
            points.append(self.get_point(position))
        return points

    def get_point(self, position):
        x, y, z = position
        cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
        extended_blocks = self.chunks[cx, cy].extended_blocks
        return extended_blocks[x % self.CHUNK_SIZE, y % self.CHUNK_SIZE, z]
    
    def get_neighbors(self, point): # make it return all, not only unremoved
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
                    point = self.get_point(neighbor_position)
                    points.append(point)
        else: # inside chunk
            # all points present
            cx, cy = x / self.CHUNK_SIZE, y / self.CHUNK_SIZE
            extended_blocks = self.chunks[cx, cy].extended_blocks
            for deltax, deltay, deltaz in self.NEIGHBORS:
                neighbor_chunk_position = (adjx + deltax, adjy + deltay, z + deltaz) 
                point = extended_blocks[neighbor_chunk_position]
                points.append(point)
        return points
    
    def remove_point(self, point):
        point[Block.VERIFIED] = True
    
    def contains(self, position):
        x, y, z = position
        if (x / self.CHUNK_SIZE, y / self.CHUNK_SIZE) in self.chunks and 0 <= z < 128:
            return True
        return False

    def unremoved_point(self, point):
     # not already removed nor wall
        return not point[Block.VERIFIED] and not point[Block.DISTANCE_FROM_WALL] == 0

    def unremoved_position(self, position):
        if self.contains(position):
            return self.unremoved_point(self.get_point(position))
        else:
            return False

    def check(self):
        self.checking = True
        for point in self.unremoved:
            if not self.is_local_peak(point, self.get_neighbors(point)):
                if self.is_expendable(point, self.get_neighbors(point)):
                    print point, self.get_neighbors(point)


    is_expendable = dim3_connected4_expendable


class ProgressiveMCDistanceThinner(ProgressiveDistanceThinner):
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def __init__(self, chunks):
        points = {}
        self.chunks = chunks
        for (cx, cy), chunk in chunks.items():
            extended_blocks = chunk.extended_blocks
            for block in extended_blocks.flat:
                if Block.is_air(block) and block[Block.VISITED]:
                    distance_from_wall = block[Block.DISTANCE_FROM_WALL]
                    x, y, z = block[Block.POSITION]
                    points[(x, y, z)] = block
                block[Block.VISITED] = False
        ProgressiveDistanceThinner.__init__(self, points)
        
    def get_neighbors(self, point):
        x, y, z = point[Block.POSITION]
        neighbors = []
        for deltax, deltay, deltaz in self.NEIGHBORS:
            neighbor_position = (x + deltax, y + deltay, z + deltaz)
            if self.contains(neighbor_position):
                neighbors.append(self.points[neighbor_position])
        return neighbors
    
    def contains(self, position):
        return position in self.points

    is_expendable = dim3_connected4_expendable
    

class ImageDistanceThinner(DistanceThinner):
    def get_neighbors(self, point):
        xpos, ypos = point.position
        neighbors = []
        for position in [                 (xpos, ypos - 1),
                         (xpos - 1, ypos),                 (xpos + 1, ypos),
                                          (xpos, ypos + 1),                 ]:
            if position in self.points:
                neighbors.append(self.points[position])
        return neighbors

    def is_expendable(self, point, neighbors):
        #print point, neighbors
        #raw_input()
        
        if len(neighbors) == 0:
            raise Exception("no neighbors")
        
        #check if otherwise expendable
        
        if len(neighbors) == 1:
            # This is responsible for hooking into ends of tunels.
            # If this is the peak, then we hit an elongated maximum field.
            # It's quite possible a tunnel has parallel walls, and we want to keep its end.
            #
            # If the field of local maxima is wider than 1, then some "biting in" may occur.
            # In that case, appendices may be created that will have 1 neighbor only.
            # These appendices can only be 1-long in 2D, since the local maximum field will
            # not be wider than 2. If it was 3, a local maximum would be created in the middle instead
            
            # AND IT DOESN'T WORK! equality fields can happen in caves where one point is connected to 
            # something bigger and others are not.
            # 
            # return not self.is_local_maximum(point, neighbors)
            
            return True
        
        if len(neighbors) == 2: # Two possibilities: corner or connection
            posx0, posy0 = neighbors[0].position
            posx1, posy1 = neighbors[1].position
            
            if not (abs(posx0 - posx1) == 2 or abs(posy0 - posy1) == 2): # if neighbors not opposite to each other, i.e. distances differ by 2
                # now check if removal causes disconnections.
                # There will be no disconections if there exists another point neighboring both neighbors.
                # Because thinning works from lowest to highest distance, that point will never be closer to wall
                posx, posy = point.position
                insider_position = (posx0 - (posx - posx1)), (posy0 - (posy - posy1))
                if insider_position in self.points: # there is another point connecting the same way
                    return True # feel free to remove me
        
        elif len(neighbors) == 3:
            # One possibility: on an edge. If both opposite neighbors are connected to the third neighbor, then this block isn't necessary.
            
            posx, posy = point.position
            na = neighbors[0]
            nb = neighbors[1]
            nc = neighbors[2]
            
            connecting_points = 0
            for neighbor0, neighbor1 in ((na, nb), (nb, nc), (na, nc)):
                posx0, posy0 = neighbor0.position
                posx1, posy1 = neighbor1.position
                if not (abs(posx0 - posx1) == 2 or abs(posy0 - posy1) == 2): # if neighbors not opposite to each other, i.e. distances differ by 2
                    # then they are cornering
                    insider_position = (posx0 - (posx - posx1)), (posy0 - (posy - posy1))
                    if insider_position in self.points: # there is another point connecting the same way
                        connecting_points += 1
                        
            if connecting_points == 2:
                return True
        
        return False # unknown case, should stay

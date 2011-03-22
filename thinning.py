class DistanceThinner:
    def __init__(self, points):
        self.points = points

    def is_local_peak(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor.distance_from_wall >= point.distance_from_wall:
                return False
        return True
    
    def is_local_maximum(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor.distance_from_wall > point.distance_from_wall:
                return False
        return True

    def get_sorted_points(self): # can be optimized
        distances = {}
        for position, point in self.points.items():
            distance = point.distance_from_wall
            if distance not in distances:
                distances[point.distance_from_wall] = set()
            distances[point.distance_from_wall].add(point)
        return distances

    def perform_thinning(self):
        print
        print 'sorting {0} points into layers'.format(len(self.points))
        
        distances = self.get_sorted_points()
        
        if 0 in distances: # there are walls in it
            for point in distances[0]:
                del self.points[point.position]
            del distances[0]
        
        total_points = len(self.points)
        
        print 'thinning {0} points'.format(total_points)
        print
        
        peaks = []
        unremoved = set()
        
        for distance in sorted(distances.keys()):
            points = unremoved.union(distances[distance])
            
            print 'max distance {0}, points: on the edge {1}, previously untouched {2},\n' \
                  '\t---- total {3}'.format(distance, len(distances[distance]), len(unremoved), len(points))
            modified = True
            #for point in points:
             #   point.set_red(127)

            deleted = 0
            i = 0

            while modified:
                i += 1
                #iterdel = 0
                modified = False
                for point in list(points):
                    neighbors = self.get_neighbors(point)
                    
                    if self.is_local_peak(point, neighbors):
                        points.remove(point)
                        peaks.append(point)
                        #point.mark_maximum()
                    elif self.is_expendable(point, neighbors):
                        del self.points[point.position] # deletion must be immediate. otherwise two neighboring maxima would both either stay or erase
                        points.remove(point)
                        #point.mark_removed()
                        modified = True
                        deleted += 1
                 #       iterdel += 1
                    else: # point is not maximum but had to stay
                        pass
                #print '\t\t{0}: removed {1}'.format(i, iterdel)
                #self.image.save('thin-' + str(distance) + '-' + str(i) + '.png')
            unremoved = points
            if distance < 10:            
                print '\tRemoved {0} points in {1} iterations, left {2}'.format(deleted, i, len(unremoved))
                #self.image.save('thin-' + str(distance) + '.png')
            #raw_input()
        for point in unremoved:
            point.mark_final()
        
        print 'Thinning finished with {0} points left out of {1}'.format(len(unremoved), total_points)
        self.unremoved = unremoved
        self.peaks = peaks
        
        
class MCDistanceThinner(DistanceThinner):
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def get_neighbors(self, point):
        x, y, z = point.position
        neighbors = []
        for deltax, deltay, deltaz in self.NEIGHBORS:
            neighbor_position = (x + deltax, y + deltay, z + deltaz)
            if neighbor_position in self.points:
                neighbors.append(self.points[neighbor_position])
        return neighbors
    
    def is_expendable(self, point, neighbors):
        if len(neighbors) == 0:
            raise Exception("no neighbors! can't happen, the code is too stupid to allow these situations, let alone handle them")
        
        if len(neighbors) == 1:
            return True
        
        if len(neighbors) == 2: # Two possibilities: corner or connection
            posx0, posy0, posz0 = neighbors[0].position
            posx1, posy1, posz1 = neighbors[1].position
            
            if abs(posx0 - posx1) == 2 or abs(posy0 - posy1) == 2 or abs(posz0 - posz1) == 2: # if neighbors opposite to each other, i.e. distances differ by 2
                return False # connection inside a line
            
            # Point lies on a corner: now check if removal causes disconnections.
            # There will be no disconections if there exists another point neighboring both neighbors.
            # Because thinning works from lowest to highest distance, that point will never be closer to wall
            posx, posy, posz = point.position
            insider_position = (posx0 - (posx - posx1), posy0 - (posy - posy1), posz0 - (posz - posz1)) # TODO: check if valid
            if insider_position in self.points: # there is another point connecting the same way
                return True # feel free to remove me     
            else:
                return False
        
        elif len(neighbors) == 3: # 2 options: either corner or flat
            #posx, posy, posz = point.position
            posx0, posy0, posz0 = neighbors[0].position
            posx1, posy1, posz1 = neighbors[1].position
            posx2, posy2, posz2 = neighbors[2].position
            
            maxx, minx = max(posx0, posx1, posx2), min(posx0, posx1, posx2)
            maxy, miny = max(posy0, posy1, posy2), min(posy0, posy1, posy2)
            maxz, minz = max(posz0, posz1, posz2), min(posz0, posz1, posz2)
            
            for x in range(minx, maxx + 1):
                for y in range(miny, maxy + 1):
                    for z in range(minz, maxz + 1):
                        if not (x, y, z) in self.points:
                            return False # this point looks like a connector
            return True # this point is a part of a solid block of 6 (if flat) or 4 (if 3D)
       
        elif len(neighbors) == 6:
            return False
        
        else:
            # 5 or 4

            #posx, posy, posz = point.position

#            for neighbor in neighbors:
 #               print neighbor.position 
            
            positions = zip(*(neighbor.position for neighbor in neighbors))
  #          print positions
            maxima, minima = map(max, positions), map(min, positions)
   #         print maxima
    #        print minima
            if len(neighbors) == 4: # 2 options: cross or part of block
                if 0 in minima: # cross connection. removal will make a hole
                    return False
                
            for x in range(minima[0], maxima[0] + 1):
                for y in range(minima[1], maxima[1] + 1):
                    for z in range(minima[2], maxima[2] + 1):
                        if not (x, y, z) in self.points:
                            return False # this point looks like a connector
            return True # this point is a part of a solid block and is exposed on one side
        return False # unknown case...


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

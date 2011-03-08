class DistanceThinner:
    def __init__(self, points):
        self.points = points

    def is_maximum(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor.distance_from_wall >= point.distance_from_wall:
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
        print 'sorting layers'
        distances = self.get_sorted_points()
        
        print 'thinning'
        print
        
        maxima = []
        unremoved = set()
        
        for distance in sorted(distances.keys()):
            points = unremoved.union(distances[distance])
            
            print 'max distance {0}, points: on the edge {1}, previously untouched {2},\n' \
                  '\t---- total {3}'.format(distance, len(distances[distance]), len(unremoved), len(points))
            modified = True
            for point in points:
                point.set_red(127)

            deleted = 0
            i = 0

            while modified:
                i += 1
                modified = False
                for point in list(points):
                    neighbors = self.get_neighbors(point)
                    
                    if self.is_maximum(point, neighbors):
                        points.remove(point)
                        maxima.append(point)
                    elif self.is_expendable(point, neighbors):
                        del self.points[point.position] # deletion must be immediate. otherwise two neighboring maxima would both either stay or erase
                        points.remove(point)
                        point.set_blue(127)
                        modified = True
                        deleted += 1
                    else: # point is not maximum but had to stay
                        pass
            unremoved = points
            
            print '\tRemoved {0} points in {1} iterations, left {2}'.format(deleted, i, len(unremoved))
            self.image.save('thin-' + str(distance) + '.png')
            raw_input()


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

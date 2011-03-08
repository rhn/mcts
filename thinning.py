class DistanceThinner:
    def __init__(self, points):
        self.points = points

    def is_maximum(self, point, neighbors):
        for neighbor in neighbors:
            if neighbor.distance_from_wall > point.distance_from_wall:
                return False
        return True

    def get_sorted_points(self): # can be optimized
        distances = {}
        for position, point in self.points.items():
            distance = point.distance_from_walls
            if distance not in distances:
                distances[point.distance_from_walls] = []
            distances[point.distance_from_walls].append((position, point))
        return distances

    def perform_thinning(self):
        points_by_distance = self.get_sorted_points()
        
        print
        print 'thinning'
        print
        
        for distance in sorted(distances.keys()):
            points = distances[distance]
            print 'distance {0}, points on the edge: {1}'.format(distance, len(points))
            modified = True
            for position, point in points:
                point.set_red(0)

            deleted = 0
            i = 0

            while modified:
                i += 1
                modified = False
                for position, point in points.items():
                    if self.is_expendable(point):
                        del self.points[position] # deletion must be immediate. otherwise two neighboring maxima would both either stay or erase
                        del points[position]
                        point.set_red(255)
                        modified = True
                        deleted += 1
            print '\tRemoved {0} points in {1} iterations'.format(deleted, i)
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

    def is_expendable(self, point):
        neighbors = self.get_neighbors(point)
        if len(neighbors) == 0:
            raise Exception("no neighbors")
        
        if self.is_maximum(point, neighbors):
            return False
        
        #check if otherwise expendable
        
        if len(neighbors) == 1:
            return True
        
        if len(neighbors) == 2: # only if it's on corner
            posx0, posy0 = neighbors[0].position
            posx1, posy1 = neighbors[1].position
            if not (abs(posx0 - posx1) == 2 or abs(posy0 - posy1) == 2): # if neighbors not opposite to each other, i.e. distances differ by 2
                # now check if removal causes disconnections.
                # There will be no disconections if there exists another point neighboring both neighbors.
                # Because thinning works from lowest to highest distance, that point will never be closer to wall
                posx, posy = position
                insider_position = (posx0 - (posx - posx1)), (poxy0 - (posy - posy1))
                if insider_position in self.points: # there is another point connecting the same way
                    return True # feel free to remove me
        return False # unknown case, should stay

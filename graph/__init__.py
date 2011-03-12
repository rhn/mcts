import graph.backend as backend


def dilate(layer, get_neighbors):
    new_layer = set()
    for point in layer:
        for neighbor in get_neighbors(point):
            new_layer.add(neighbor)
    return new_layer


class Tunnel:
    def __init__(self, start, end, data=None):
        self.start = start
        self.end = end
        self.data = data

    def __repr__(self):
        return 'T(' + str(self.start) + ', ' + str(self.end) + ')'
        
class TunnelEdge(backend.Edge):
    def __init__(self, tunnel):
        backend.Edge.__init__(self, tunnel.start.node, tunnel.end.node)


class Node(backend.Node):
    def __init__(self, junction):
        backend.Node.__init__(self, str(junction))#str(junction.distance_from_wall))
        junction.node = self


class EndingNode(Node):
    def __init__(self, ending):
        Node.__init__(self, ending)
#        self.set_size(3)
        self.set_fill_color((255, 0, 0))
    
    def set_size(self, size):
        return Node.set_size(self, (size, size))


class JunctionNode(Node):
    def __init__(self, junction):
        Node.__init__(self, junction)
#        self.set_size_width(junction.distance_from_wall)


class Grapher:
    def __init__(self, points):
        self.points = points  
        
    def find_endings(self):
        for position, point in self.points.items():
            neighbors = self.get_neighbors(point)
            if len(neighbors) == 1:
                yield point
    
    def find_junctions(self):
        for position, point in self.points.items():
            neighbors = self.get_neighbors(point)
            if len(neighbors) > 2:
                yield point
    
    def get_neighbors(self, point):
        """Copied from thinning"""
        xpos, ypos = point.position
        neighbors = []
        for position in [                 (xpos, ypos - 1),
                         (xpos - 1, ypos),                 (xpos + 1, ypos),
                                          (xpos, ypos + 1),                 ]:
            if position in self.points:
                neighbors.append(self.points[position])
        return neighbors
        
    def find_tunnel(self, beginning, tentacle):
        # dimension-agnostic!
        finish = None

        previous = beginning
        while True:
            green = tentacle.value[1]
            if green != 0:
                green = 0
            else:
                green = 255
            tentacle.set_green(green)
            if tentacle.visited:
                finish = tentacle
                break

            neighbors = self.get_neighbors(tentacle)
            if len(neighbors) != 2:
                finish = tentacle
                break
            n1, n2 = neighbors
            if n1 is previous:
                next = n2
            else:
                next = n1
            
            previous, tentacle = tentacle, next
        
        self.image.save('tunnel-' + str(self.tunnelno) + '.png')
        return Tunnel(beginning, finish), finish
        
    
    def find_structure(self, point):
        """depth-first search of all nodes, extracts junctions and tunnels"""
        junctions = []
        tunnels = []
        self.tunnelno = 0
        unchecked_points = [point]
        
        while unchecked_points:
            points_to_check = unchecked_points
            unchecked_points = []
            for point in points_to_check:
                junctions.append(point)
                point.visited = True

                for tentacle in self.get_neighbors(point):
                    tunnel, ending = self.find_tunnel(point, tentacle)
                    self.tunnelno += 1
                    tunnels.append(tunnel)
                    if not ending.visited:
                        unchecked_points.append(ending)
                        
        return junctions, tunnels
        
    def extract_features(self, junctions, tunnels):
        # this line is a good place to simplify junctions into huge caves or worlds
    
        nodes = []
        edges = []
        
        for junction in junctions:
            neighbors_count = len(self.get_neighbors(junction))
            if neighbors_count == 1:
                node = EndingNode(junction)
            elif neighbors_count == 2:
                raise ValueError("impossible! 2 neighbors.", junction)
            else:
                node = JunctionNode(junction)
            nodes.append(node)      
                
        for tunnel in tunnels:
            edges.append(TunnelEdge(tunnel))
        return nodes, edges  
    
    def make_graph(self):
        """Must have at least 1 junction or ending"""
        start_point = None
        for position, point in self.points.items():
            point.visited = False
        for ending in self.find_endings():
            start_point = ending
            break
            
        if start_point is None:
            for junction in self.find_junctions():
               start_point = junction
               break
        
        junctions, tunnels = self.find_structure(start_point)
        
        print tunnels
        
        nodes, edges = self.extract_features(junctions, tunnels)
        backend.save('map.png', nodes, edges)

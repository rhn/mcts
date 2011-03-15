import graph.backend as backend


def dilate(layer, get_neighbors):
    new_layer = set()
    for point in layer:
        for neighbor in get_neighbors(point):
            new_layer.add(neighbor)
    return new_layer


class Tunnel:
    def __init__(self, start, end, start_neighbor, end_neighbor, data=None):
        self.start = start
        self.end = end
        self.start_neighbor = start_neighbor
        self.end_neighbor = end_neighbor
        self.data = data
        
    def __eq__(self, tunnel):
        try:
            other_start = tunnel.start
            other_end = tunnel.end
            other_start_neighbor = tunnel.start_neighbor
            other_end_neighbor = tunnel.end_neighbor
        except AttributeError:
            return False
        if self.start != other_start:
            other_start, other_end = other_end, other_start
            other_start_neighbor, other_end_neighbor = other_end_neighbor, other_start_neighbor
        return self.start == other_start and self.end == other_end and self.start_neighbor == other_start_neighbor and self.end_neighbor == other_end_neighbor

    def __repr__(self):
        return 'T(' + str(self.start) + ', ' + str(self.end) + ')'
        
        
class TunnelEdge(backend.Edge):
    def __init__(self, tunnel):
        backend.Edge.__init__(self, tunnel.start.node.diagram_node, tunnel.end.node.diagram_node)


class Node:
    def __init__(self, points):
        self.points = points
        self.diagram_node = None
    
    def get_diagram_representation(self):
        raise NotImplementedError
    
    def __repr__(self):
        return str(self.points[0])


def tunnel_in_container(container, tunnel):
    for element in container:
        if tunnel == element:
            return True
    return False


class Grapher:
    def __init__(self, points):
        self.points = points  
    
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
        
    def find_tunnel(self, tentacle):
        # dimension-agnostic!
        beginning, direction = tentacle
        finish = None
        beginning_neighbor = direction
        
        previous = beginning
        current = beginning_neighbor
        
        while True:
            green = current.value[1]
            if green != 0:
                green = 0
            else:
                green = 255
            current.set_green(green)

            neighbors = self.get_neighbors(current)
            if len(neighbors) != 2:
                finish = current
                break

            n1, n2 = neighbors
            if n1 is previous:
                next = n2
            else:
                next = n1
            
            previous, current = current, next
        
        end_neighbor = previous
#        self.image.save('tunnel-' + str(self.tunnelno) + '.png')
        return Tunnel(beginning, finish, beginning_neighbor, end_neighbor), finish
        
    def mark_clump(self, point):
        """Finds connected points that are not part of tunnels, assigns a single
        node for all of them and returns the node.
        """
        # TODO: flood fill it properly
        node = Node([point])
        point.node = node
    
    def get_node_neighbors(self, node):
        neighbors = []
        for point in node.points:
            for neighbor in self.get_neighbors(point):
                if neighbor.node != node:
                    neighbors.append((point, neighbor))
        return neighbors
    
    def find_structure(self):
        """depth-first search of all points, extracts junctions(nodes) and tunnels"""
        
        starting_point = None
        # firse initalize points
        for point in self.points.values():
            point.node = None
            neighbors = self.get_neighbors(point)
            if len(neighbors) != 2:
                starting_point = point
        
        if starting_point is None:
            raise Exception("Couldn't detect any junction in the thinned map.")
        
        clumps = []
        tunnels = []
        self.tunnelno = 0
        unchecked_points = [starting_point]
        
        while unchecked_points:
            points_to_check = unchecked_points
            unchecked_points = []
#            print 'and again'
            for point in points_to_check:
 #               print point
  #              if point.node:
   #                 raise Exception("jak nie zonk, to co?")
                self.mark_clump(point)
                clumps.append(point.node)

                for tentacle in self.get_node_neighbors(point.node):
                    # tentacle is a pair of points: beginning, direction
                    tunnel, ending = self.find_tunnel(tentacle)
                    self.tunnelno += 1
                    if not tunnel_in_container(tunnels, tunnel):
                        tunnels.append(tunnel)
                    if ending.node is None and ending not in points_to_check:
    #                    print '\tadding', ending
                        unchecked_points.append(ending)
#                    raw_input()
                        
        return clumps, tunnels
        
        
    def extract_diagram(self, clumps, tunnels):
        nodes = []
        edges = []
        endings = 0
        junctions = 0
        
        for clump in clumps:
            # move this code to clump.get_diagram_representation()
            neighbors_count = len(self.get_node_neighbors(clump))
            if neighbors_count == 1:
                node = backend.EndingNode(clump)
                endings += 1
            elif neighbors_count == 2:
                raise ValueError("impossible! 2 neighbors.", clump)
            else:
                node = backend.JunctionNode(clump)
                junctions += 1
            clump.diagram_node = node
            nodes.append(node)      
        print '{0} endings and {1} junctions'.format(endings, junctions)
        for tunnel in tunnels:
            edges.append(TunnelEdge(tunnel))
        return nodes, edges  
    
    
    def make_graph(self):
        """Must have at least 1 junction or ending"""
        
        clumps, tunnels = self.find_structure()

#        print clumps        
        print 'found {0} tunnels and {1} clumps'.format(len(tunnels), len(clumps))
        
        nodes, edges = self.extract_diagram(clumps, tunnels)

        print 'found {0} edges connecting {1} nodes'.format(len(edges), len(nodes))
        backend.save('map.png', nodes, edges)

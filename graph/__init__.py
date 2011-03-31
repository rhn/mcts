import graph.backend as backend
import common
import pymclevel as mclevel

class Tunnel: # could be sort of a partially-mutable object for set lookup. start* and end* are never going to change
    def __init__(self, start, end, start_neighbor, end_neighbor, data=None):
        self.start = start
        self.end = end
        self.start_neighbor = start_neighbor
        self.end_neighbor = end_neighbor
        self.data = data
    
    def merge_endpoints(self):
        points = self.start.node.points + self.end.node.points
        # TODO: merge node data, add tunnel data (points?) would be nice for volume calc
        # TODO: find the best class after joining:
        #    DE  J   C   W
        # DE C   J/C C   W
        # J      J/C C   W
        # C          C   W
        # W              W
        clump = Cave(points)
        for point in points:
            point.node = clump
        return clump
    
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
        backend.Edge.__init__(self, tunnel.start.node.get_root_diagram_node(), tunnel.end.node.get_root_diagram_node())


class Clump:
    NAME = 'N'
    def __init__(self, points):
        self.points = points
        self._root_diagram_node = None
        self._diagram_representation = None
    
    def get_diagram_representation(self):
        if self._diagram_representation is None:
            self._create_diagram_representation()
        return self._diagram_representation
    
    def get_root_diagram_node(self):
        if self._root_diagram_node is None:
            self._create_diagram_representation()
        return self._root_diagram_node
    
    def get_avg_size(self):
        size = 0
        for point in self.points:
            size += point.distance_from_wall
        return size / len(self.points)
    
    def get_avg_position(self):
        x, y, z = 0, 0, 0
        for point in self.points:
            x += point.position[0]
            y += point.position[1]
            z += point.position[2]
        return (x / len(self.points), y / len(self.points), z / len(self.points))

    def __repr__(self):
        return self.NAME + '({0}x {1}, {2})'.format(len(self.points), self.get_avg_position(), self.get_avg_size())


class DeadEnd(Clump):
    NAME = 'D'
    def _create_diagram_representation(self):
        self._root_diagram_node = backend.EndingNode(self)
        self._diagram_representation = [self._root_diagram_node], []
        
        
class Cave(Clump):
    NAME = 'C'
    def _create_diagram_representation(self):
        self._root_diagram_node = backend.JunctionNode(self)
        self._diagram_representation = [self._root_diagram_node], []


def tunnel_in_container(container, tunnel):
    """Performs a search over container using __eq__ comparison and not hash"""
    for element in container:
        if tunnel == element:
            return True
    return False


class CaveGraph:
    def __init__(self, clumps, tunnels):
        self.clumps = clumps
        self.tunnels = tunnels
        
    def get_distance(self, point1, point2):
        # 2D
        return abs(point1.position[0] - point2.position[0]) + abs(point1.position[1] - point2.position[1]) + abs(point1.position[2] - point2.position[2])

    def simplify(self):
        """Smart heuristics to join node into caves. In this implementation, if
        one endpoint of a tunnel lies within the radius of another, join them
        together.
        """
        
        added_clumps = []
        staying_tunnels = []
        removed_clumps = set()
        
        for tunnel in self.tunnels:
            tunnel_end_distance = self.get_distance(tunnel.start, tunnel.end)
            if tunnel_end_distance - tunnel.start.distance_from_wall < 0 or \
                    tunnel_end_distance - tunnel.end.distance_from_wall < 0:
                removed_clumps.add(tunnel.start.node)
                removed_clumps.add(tunnel.end.node)
                new_node = tunnel.merge_endpoints()
                added_clumps.append(new_node)
            else:
                staying_tunnels.append(tunnel)
        print removed_clumps
        
        new_clumps = []
        
        for clump in list(self.clumps) + added_clumps:
            if clump not in removed_clumps:
                new_clumps.append(clump)
            else:
                removed_clumps.remove(clump)

        if removed_clumps:
            raise Exception("Some removed clumps couldn't be found in the main set and I'm scared")
        
        self.clumps = new_clumps
        self.tunnels = staying_tunnels
#        print self.tunnels

    def extract_diagram(self):
        """Converts clumps and tunnels to graph nodes and edges to be presented
        on the final map.
        """
        nodes = []
        edges = []
        
        for clump in self.clumps:
            new_nodes, new_edges = clump.get_diagram_representation()
            nodes.extend(new_nodes)
            edges.extend(new_edges)
            #nodes.append(backend.JunctionNode(clump))
        # TODO: move to Tunnel.get_diagram_representation()
        for tunnel in self.tunnels:
#            print tunnel
            edges.append(TunnelEdge(tunnel))
        return nodes, edges
    

class SeparatePoint:
    def __init__(self, point):
        self.point = point
        self.position = tuple(point[common.Block.POSITION])
        self.node = None
        self.distance_from_wall = point[common.Block.DISTANCE_FROM_WALL]
    
    def mark_clump(self):
        self.point[common.Block.VALUE] = mclevel.materials.LapisLazuliBlock.ID
    
    def __str__(self):
        return str(self.position)

class MCGrapher:
    NEIGHBORS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    def __init__(self, points):
        self.points = {}
        for point in points:
            point = SeparatePoint(point)
            self.points[point.position] = point
    
    def get_neighbors(self, point):
        x, y, z = point.position
        neighbors = []
        for deltax, deltay, deltaz in self.NEIGHBORS:
            neighbor_position = (x + deltax, y + deltay, z + deltaz)
            if neighbor_position in self.points:
                neighbors.append(self.points[neighbor_position])
        return neighbors
        
    def find_tunnel(self, tentacle):
        # dimension-agnostic!
        beginning, direction = tentacle
        finish = None
        beginning_neighbor = direction

        previous = beginning
        current = beginning_neighbor
        
        while True:
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
        """Finds connected points that are not part of tunnels and assigns a
        single node for all of them.
        """
        # TODO: flood fill it properly
        if point.node:
            return
        neighbors = len(self.get_neighbors(point))
        if neighbors == 1:
            node = DeadEnd([point])
        elif neighbors == 2:
            raise Exception("WTF, 2 neighbors")
        else:
            node = Cave([point])
        point.node = node
    
    def get_node_neighbors(self, node):
        """Returns "tentacles": pairs of (point, neighbor) where point belongs
        to node and neighbor doesn't.
        """
        neighbors = []
        for point in node.points:
            for neighbor in self.get_neighbors(point):
                if neighbor.node != node:
                    neighbors.append((point, neighbor))
        return neighbors
    
    def find_structure(self):
        """Depth-first graph traversal, extracts clumps (nodes) and tunnels
        (edges). Graph must have at least one point that is a junction.
        """
        
        starting_point = None
        # firse initalize points
        for point in self.points.values():
            point.node = None
            neighbors = self.get_neighbors(point)
            if len(neighbors) != 2:
                starting_point = point
        
        if starting_point is None:
            raise Exception("Couldn't detect any junction in the thinned map.")
        
        clumps = set()
        tunnels = []
        self.tunnelno = 0
        unchecked_points = [starting_point]
        
        while unchecked_points:
            points_to_check = unchecked_points
            unchecked_points = []
#            print 'and again'
            for point in points_to_check:
                print point
               # if point.node:
                #    raise Exception("jak nie zonk, to co?")
                point.mark_clump()
                self.mark_clump(point)
                clumps.add(point.node)
                print point.node
                for tentacle in self.get_node_neighbors(point.node):
                    # tentacle is a pair of points: beginning, direction
                    tunnel, ending = self.find_tunnel(tentacle)
                    print tunnel
                    self.tunnelno += 1
                    if not tunnel_in_container(tunnels, tunnel):
                        tunnels.append(tunnel)
                    else:
                        print 'rejected'
                    if ending.node is None and ending not in points_to_check:
    #                    print '\tadding', ending
                        unchecked_points.append(ending)
                print len(clumps), len(tunnels)
                raw_input()
        raw_input()
        return CaveGraph(clumps, tunnels)
    
    
    def make_graph(self):
        cave_graph = self.find_structure()
        print 'found {0} tunnels and {1} clumps'.format(len(cave_graph.tunnels), len(cave_graph.clumps))
        cave_graph.simplify()

        print 'simplified to {0} tunnels and {1} clumps'.format(len(cave_graph.tunnels), len(cave_graph.clumps))
        
        nodes, edges = cave_graph.extract_diagram()

        print 'resulting image will be composed of {0} edges connecting {1} nodes'.format(len(edges), len(nodes))
#        print edges
        backend.save('map.png', nodes, edges)

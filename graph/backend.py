import pydot

class Node(pydot.Node):
    scale = 30
    def __init__(self, name):
        pydot.Node.__init__(self, name)
        self.set_fill_color(None)
    
    def set_size(self, size):
        self.set('width', str(size[0] / self.scale))
        self.set('height', str(size[1] / self.scale))
        
    def set_size_width(self, width):
        self.set('width', str(width / self.scale))
    
    def set_fill_color(self, color):
        if color is None:
            self.set('style', '')
        else:
            strcolor = '#' + ''.join((hex(component)[2:].zfill(2) for component in color))
            
            self.set('style', 'filled')
            self.set('fillcolor', strcolor)
    
    def set_position(self, x, y):
        posstr = '"{0},{1}"'.format(x / self.scale, y / self.scale)
        self.set('pos', posstr)
    
    def set_pinned(self, value):
        if value:
            strval = 'true'
        else:
            strval = 'false'
        self.set('pin', strval)
    
    def set_label(self, value):
        self.set('label', value)
      
      
class Edge(pydot.Edge):
    def __init__(self, src, dst, directed=False):
        pydot.Edge.__init__(self, src, dst)
        self.set('dir', 'none')
        
        
def save(filename, nodes, edges):
    graph = pydot.Dot()
    for node in nodes:
        graph.add_node(node)
    for edge in edges:
        graph.add_edge(edge)
    try:
        with open(filename, 'w') as output:
            output.write(graph.create(prog='neato -s', format='png'))
    except Exception, e:
        import traceback
        traceback.print_exc(e)
        print 'Exception occured. Saving dot file to', filename + '.dot'
        with open(filename + '.dot', 'w') as output:
            output.write(graph.create(format='raw'))
    return graph
    
    
class ClumpNode(Node):
    def __init__(self, clump, size):
        Node.__init__(self, str(clump))#str(junction.distance_from_wall))
        self.set_size(3)
        self.set_label(str(size))

    def set_size(self, size):
        return Node.set_size(self, (size, size))


class EndingNode(ClumpNode):
    def __init__(self, ending, size):
        ClumpNode.__init__(self, ending, size)
        self.set_fill_color((255, 0, 0))
    

class JunctionNode(ClumpNode):
    def __init__(self, junction, size):
        ClumpNode.__init__(self, junction, size)
#        self.set_size_width(junction.distance_from_wall)


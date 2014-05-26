### GRAPH ############################################################################################

# The NodeBox Graph library includes algorithms from NetworkX for 
# betweenness centrality and eigenvector centrality, Connelly Barnes' implementation of 
# Dijksta shortest paths (here) and the spring layout for JavaScript by Aslak Hellesoy 
# and Dave Hoover (here). The goal of this library is visualization of small graphs (<200 elements), 
# if you need something more robust we recommend using NetworkX.

### CREDITS ##########################################################################################

# Copyright (c) 2008 Tom De Smedt.
# See LICENSE.txt for details.

__author__    = "Tom De Smedt"
__version__   = "1.9.5.6"
__copyright__ = "Copyright (c) 2008 Tom De Smedt"
__license__   = "GPL"

######################################################################################################

import cluster
import event
import layout
import proximity
import style
import numpy as np
import time

#### GRAPH NODE ######################################################################################

class node:
    
    def __init__(self, graph, id="", radius=8, style=style.DEFAULT, category="", label=None,
                 properties={}):
        
        """ A node with a unique id in the graph.
        Its position is calculated by graph.layout.
        The node's radius and style define how it looks onscreen.
        """

        self.graph = graph
        self.id = id
        self.category = category
        self.label = label or self.id
        self.links = links()
        self.vx = 0
        self.vy = 0
        self.force = layout.Point(0, 0)
        self.r = radius
        self.style = style
        
        self._visited = False
        
        self._betweenness = None
        self._eigenvalue = None
        
        for k, v in properties.items():
            if not k in self.__dict__:
                self.__dict__[k] = v

    def _edges(self):
        e = []
        for d in self.links._edges.values():
            e = e + d.values()
        return e
        #return self.links._edges.values()

    edges = property(_edges)
    
    def _is_leaf(self):
        return len(self.links) == 1
    
    is_leaf = property(_is_leaf)
    
    def can_reach(self, node, traversable=lambda node, edge: True):
        
        """ Returns True if given node can be reached over traversable edges.
        To enforce edge direction, use a node==edge.node1 traversable.
        """
        
        if isinstance(node, str):
            node = self.graph[node]
        for n in self.graph.nodes:
            n._visited = False
        return proximity.depth_first_search(self,
            visit=lambda n: node == n,
            traversable=traversable
            )
    
    def _get_betweenness(self):
        if self._betweenness == None:
            self.graph.betweenness_centrality()
        return self._betweenness
        
    betweenness = property(_get_betweenness)
    traffic = betweenness

    def _get_eigenvalue(self):
        if self._eigenvalue == None:
            self.graph.eigenvector_centrality()
        return self._eigenvalue
        
    eigenvalue = property(_get_eigenvalue)
    weight = eigenvalue
    
    def _x(self): return self.vx * self.graph.d
    def _y(self): return self.vy * self.graph.d
    x = property(_x)
    y = property(_y)
    
    def __contains__(self, pt):
        
        """ True if pt.x, pt.y is inside the node's absolute position.
        """

        if abs(self.graph.x+self.x-pt.x) < self.r*2 and \
           abs(self.graph.y+self.y-pt.y) < self.r*2:
            return True
        else:
            return False
        
    def flatten(self, distance=1):
        return cluster.flatten(self, distance)
    
    def __and__(self, node, distance=1):
        return cluster.intersection(
            self.flatten(distance), node.flatten(distance))

    def __or__(self, node, distance=1):
        return cluster.union(
            self.flatten(distance), node.flatten(distance))
    
    def __sub__(self, node, distance=1):
        return cluster.difference(
            self.flatten(distance), node.flatten(distance))
    
    def __repr__(self): 
        try: return "<"+str(self.id)+" node>"
        except:
            return "<"+self.id.encode("utf-8")+" node>"

    def __str__(self): 
        try: return str(self.id)
        except:
            return self.id.encode("utf-8")
            
    def __eq__(self, node):
        if not isinstance(node, self.__class__): return False
        return self.id == node.id

#### GRAPH NODE LINKS ################################################################################

class links(list):
    
    """ A list in which each node has an associated edge.
    The edge() method returns the edge for a given node id.
    """
    
    def __init__(self): 
        self._edges = dict()
    
    def append(self, node, edge): 
        if not self._edges.has_key(node.id):
            self._edges[node.id] = {}
        self._edges[node.id][edge.label] = edge
        if not (node in self):
            list.append(self, node)

    def remove(self, node, label):
        if self._edges.has_key(node.id): 
            if self._edges[node.id].has_key(label):
                del self._edges[node.id][label]
            if len(self._edges[node.id].keys()) == 0:
                del self._edges[node.id]
                list.remove(self, node)

    #def edge(self, id): 
    #    if isinstance(id, node): 
    #        id = id.id
    #    return self._edges[id]

    def edge(self, a, label):
        if isinstance(a, node):
            node_id = a.id
        else:
            node_id = a
        return self._edges[node_id][label]

    def edges(self, id):
        if isinstance(id, node): 
            id = id.id
        return self._edges[id].values()

    def has_edge(self, node_name, label):
        if self._edges.has_key(node_name) and self._edges[node_name].has_key(label):
            return True
        else:
            return False

##### GRAPH EDGE #####################################################################################

class edge(object):
    
    def __init__(self, graph, node1, node2, weight=0.0, length=1.0, label="", properties={}):

        self.node1  = node1
        self.node2  = node2
        self.weight = weight
        self.length = length
        self.label  = label
        self.graph  = graph
        
        for k, v in properties.items():
            if not k in self.__dict__:
                self.__dict__[k] = v
    
    def _get_length(self): 
        return self._length

    def _set_length(self, v): 
        self._length = max(0.1, v)

    def __contains__(self, pt):
        """ 
            True if pt.x, pt.y is inside the edge's line (doesn't work for arbitary curves)
        """

        p0 = np.matrix([self.node1.x, self.node1.y]).T
        p1 = np.matrix([self.node2.x, self.node2.y]).T
        gp = np.matrix([self.graph.x, self.graph.y]).T
        p  = np.matrix([pt.x, pt.y]).T - gp
        A  = p1 - p0
        x_hat = np.linalg.inv(A.T * A) * A.T * (p - p0)
        projected = p0 + (A * x_hat)
        distance = np.linalg.norm(projected - p)
        if distance < 10 and x_hat > 0. and x_hat < 1.0:
            return True
        else:
            return False

    length = property(_get_length, _set_length)

#### GRAPH ###########################################################################################

LAYOUT_CIRCLE = "circle"
LAYOUT_SPRING = "spring"
layout_ = layout # there's also a "layout" parameter in graph.__init__()

class graph(dict):
    
    def __init__(self, iterations=1000, distance=1.0, layout=LAYOUT_SPRING):
        
        self.nodes = []
        self.edges = []
        self.root  = None
        
        # Calculates positions for nodes.
        self.layout = layout_.__dict__[layout+"_layout"](self, iterations)
        self.d = node(None).r * 2.5 * distance
        
        # Hover, click and drag event handler.
        self.events = event.events(self, _ctx)
        
        # Enhanced dictionary of all styles.
        self.styles = style.styles(self)
        self.styles.append(style.style(style.DEFAULT, _ctx))
        self.alpha = 0

        # Try to specialize intensive math operations.
        try:
            import psyco
            psyco.bind(self.layout._bounds)
            psyco.bind(self.layout.iterate)
            psyco.bind(self.__or__)
            psyco.bind(cluster.flatten)
            psyco.bind(cluster.subgraph)
            psyco.bind(cluster.clique)
            psyco.bind(cluster.partition)
            psyco.bind(proximity.dijkstra_shortest_path)
            psyco.bind(proximity.brandes_betweenness_centrality)
            psyco.bind(proximity.eigenvector_centrality)
            psyco.bind(style.edge_arrow)
            psyco.bind(style.edge_label)
            #print "using psyco"
        except:
            pass

        self.times = {}
        self.times['other'] = 0.
        self.times['edges'] = 0.
        self.times['nodes'] = 0.
        self.times['events'] = 0.
        self.times['path'] = 0.
        self.times['node_ids'] = 0.
        self.times['iter'] = 0

    def _get_distance(self):
        return self.d / (node(None).r * 2.5)
    def _set_distance(self, value):
        self.d = node(None).r * 2.5 * value
    distance = property(_get_distance, _set_distance)

    def copy(self, empty=False):
        
        """ Create a copy of the graph (by default with nodes and edges).
        """
        
        g = graph(self.layout.n, self.distance, self.layout.type)
        g.layout = self.layout.copy(g)
        g.styles = self.styles.copy(g)
        g.events = self.events.copy(g)

        if not empty:
            for n in self.nodes:
                g.add_node(n.id, n.r, n.style, n.category, n.label, (n == self.root), n.__dict__)
            for e in self.edges:
                g.add_edge(e.node1.id, e.node2.id, e.weight, e.length, e.label, e.__dict__)
        
        return g

    def clear(self):
        
        """ Remove nodes and edges and reset the layout.
        """
        
        dict.clear(self)
        self.nodes = []
        self.edges = []
        self.root  = None
        
        self.layout.i = 0
        self.alpha = 0
    
    def new_node(self, *args, **kwargs):
        """ Returns a node object; can be overloaded when the node class is subclassed.
        """
        return node(*args, **kwargs)

    def new_edge(self, *args, **kwargs):
        """ Returns an edge object; can be overloaded when the edge class is subclassed.
        """
        args = list(args)
        args.insert(0, self)
        args = tuple(args)
        return edge(*args, **kwargs)
    
    def add_node(self, id, radius=8, style=style.DEFAULT, category="", label=None, root=False,
                 properties={}):
        
        """ Add node from id and return the node object.
        """
        
        if self.has_key(id): 
            return self[id]
            
        if not isinstance(style, str) and style.__dict__.has_key["name"]:
            style = style.name
        
        n = self.new_node(self, id, radius, style, category, label, properties)
        self[n.id] = n
        self.nodes.append(n)
        if root: self.root = n
            
        return n
    
    def add_nodes(self, nodes):
        """ Add nodes from a list of id's.
        """
        try: [self.add_node(n) for n in nodes]
        except:
            pass
    
    def add_edge(self, id1, id2, weight=0.0, length=1.0, label="", properties={}):
        
        """ Add weighted (0.0-1.0) edge between nodes, creating them if necessary.
        The weight represents the importance of the connection (not the cost).
        """
        
        if id1 == id2: return None
        
        if not self.has_key(id1): self.add_node(id1)
        if not self.has_key(id2): self.add_node(id2)
        n1 = self[id1]
        n2 = self[id2]
        
        # If a->b already exists, don't re-create it.
        # However, b->a may still pass.
        #if n1 in n2.links:
        #    if n2.links.edge(n1).node1 == n1:
        #        return self.edge(id1, id2)

        #If a->b with label c exists don't recreate it
        if n2.links.has_edge(n1.id, label):
            return n2.edge(n1, label)
        weight = max(0.0, min(weight, 1.0))

        e = self.new_edge(n1, n2, weight, length, label, properties)
        self.edges.append(e)
        n1.links.append(n2, e)
        n2.links.append(n1, e)

        return e
        
    def remove_node(self, id):
        
        """ Remove node with given id.
        """
 
        if self.has_key(id):
            n = self[id]
            self.nodes.remove(n)
            del self[id]
            
            # Remove all edges involving id and all links to it.
            for e in list(self.edges):
                if n in (e.node1, e.node2):
                    for n1_edge in e.node1.links.edges(n):
                        e.node1.links.remove(n, n1_edge.label)
                    for n2_edge in e.node2.links.edges(n):
                        e.node2.links.remove(n, n2_edge.label)
                    #if n in e.node1.links: 
                    #    e.node1.links.remove(n)
                    #if n in e.node2.links: 
                    #    e.node2.links.remove(n)
                    self.edges.remove(e)

    def remove_edge(self, id1, id2, label):
        
        """ Remove edges between nodes with given id's.
        """
        
        for e in list(self.edges):
            if id1 in (e.node1.id, e.node2.id) and \
               id2 in (e.node1.id, e.node2.id) and\
               e.label == label:
                e.node1.links.remove(e.node2, label)
                e.node2.links.remove(e.node1, label)
                self.edges.remove(e)            

    def node(self, id):
        """ Returns the node in the graph associated with the given id.
        """
        if self.has_key(id):
            return self[id]
        return None
    
    def edge(self, id1, id2, label):
        """ Returns the edge between the nodes with given id1 and id2.
        """
        #if id1 in self and id2 in self and self[id2] in self[id1].links:
        es = self.all_edges_between(id1, id2)
        if es != None:
            for e in es:
                if e.label == label:
                    return e
        return None
        #if id1 in self and \
        #   id2 in self and \
        #   self[id2] in self[id1].links:
        #    return self[id1].links.edge(id2, label)
        #return None

    def all_edges_between(self, id1, id2):
        if id1 in self and \
           id2 in self and \
           self[id2] in self[id1].links:
            return self[id1].links.edges(id2)
        return None
    
    def __getattr__(self, a):
        
        """ Returns the node in the graph associated with the given id.
        """
        if self.has_key(a): 
            return self[a]
        raise AttributeError, "graph object has no attribute '"+str(a)+"'"
    
    def update(self, iterations=10):
        
        """ Iterates the graph layout and updates node positions.
        """    

        # The graph fades in when initially constructed.
        self.alpha += 0.05
        self.alpha = min(self.alpha, 1.0)

        # Iterates over the graph's layout.
        # Each step the graph's bounds are recalculated
        # and a number of iterations are processed,
        # more and more as the layout progresses.
        if self.layout.i == 0:
            self.layout.prepare()
            self.layout.i += 1
        elif self.layout.i == 1:
            self.layout.iterate()
        elif self.layout.i < self.layout.n:
            n = min(iterations, self.layout.i / 10 + 1)
            for i in range(n): 
                self.layout.iterate()
        
        # Calculate the absolute center of the graph.
        #if self.alpha < .9:
        min_, max = self.layout.bounds
        self.x = _ctx.WIDTH - max.x*self.d - min_.x*self.d
        self.y = _ctx.HEIGHT - max.y*self.d - min_.y*self.d
        self.x /= 2
        self.y /= 2
            
        return not self.layout.done
        
    def solve(self):
        """ Iterates the graph layout until done.
        """
        self.layout.solve()
        self.alpha = 1.0
        
    def _done(self):
        return self.layout.done
        
    done = property(_done)
    
    def offset(self, node):
        """ Returns the distance from the center to the given node.
        """
        x = self.x + node.x - _ctx.WIDTH/2
        y = self.y + node.y - _ctx.HEIGHT/2
        return x, y
    
    def draw(self, dx=0, dy=0, weighted=False, directed=False, highlight=[], traffic=None, user_draw_final=None, user_draw_start=None):
        
        """ Layout the graph incrementally.
        
        The graph is drawn at the center of the canvas.
        The weighted and directed parameters visualize edge weight and direction.
        The highlight specifies list of connected nodes. 
        The path will be colored according to the "highlight" style.
        Clicking and dragging events are monitored.
        
        """
       

        START_TIME = time.time()
        self.update()
        OTHER_TIME = time.time()

        # Draw the graph background.
        s = self.styles.default
        s.graph_background(s)

        # Center the graph on the canvas.
        _ctx.push()
        _ctx.translate(self.x+dx, self.y+dy)
 
        # Indicate betweenness centrality.
        #if traffic:
        #    if isinstance(traffic, bool): 
        #        traffic = 5
        #    for n in self.nodes_by_betweenness()[:traffic]:
        #        try: s = self.styles[n.style]
        #        except: s = self.styles.default
        #        if s.graph_traffic:
        #            s.graph_traffic(s, n, self.alpha)        

        if user_draw_start != None:
            user_draw_start()


        # Draw the edges and their labels.
        s = self.styles.default
        if s.edges:
            s.edges(s, self.edges, self.alpha, weighted, directed)
        
        EDGES_TIME = time.time()
        # Draw each node in the graph.
        # Apply individual style to each node (or default).        
        for n in self.nodes:
            try:  s = self.styles[n.style]
            except: s = self.styles.default
            if s.node:
                s.node(s, n, self.alpha)
        NODES_TIME = time.time()
        
        # Highlight the given shortest path.
        #try: s = self.styles.highlight
        #except: s = self.styles.default
        #if s.path:
        #    s.path(s, self, highlight)

        PATHS_TIME = time.time()

        # Draw node id's as labels on each node.
        for n in self.nodes:
            try:  s = self.styles[n.style]
            except: s = self.styles.default
            if s.node_label:
                s.node_label(s, n, self.alpha)
        EVENTS_TIME = time.time()

        if user_draw_final != None:
            user_draw_final()
        
        # Events for clicked and dragged nodes.
        # Nodes will resist being dragged by attraction and repulsion,
        # put the event listener on top to get more direct feedback.
        self.events.update()
        NODE_IDS_TIME = time.time()

        self.times['node_ids'] += NODE_IDS_TIME - EVENTS_TIME
        self.times['path']     += EVENTS_TIME - PATHS_TIME
        self.times['events']   += PATHS_TIME - NODES_TIME
        self.times['nodes']    += NODES_TIME - EDGES_TIME
        self.times['edges']    += EDGES_TIME - OTHER_TIME
        self.times['other']    += OTHER_TIME - START_TIME
        self.times['iter']     += 1

        #print 'node_ids',1000.0 * (self.times['node_ids'] / self.times['iter']),
        #print 'path',    1000.0 * (self.times['path']     / self.times['iter']),
        #print 'events',  1000.0 * (self.times['events']   / self.times['iter']),
        #print 'nodes',   1000.0 * (self.times['nodes']    / self.times['iter']),
        #print 'edges',   1000.0 * (self.times['edges']    / self.times['iter']),
        #print 'other',   1000.0 * (self.times['other']    / self.times['iter'])

        _ctx.pop()
    
    def prune(self, depth=0):
        """ Removes all nodes with less or equal links than depth.
        """
        for n in list(self.nodes):
            if len(n.links) <= depth:
                self.remove_node(n.id)
                
    trim = prune
    
    def shortest_path(self, id1, id2, heuristic=None, directed=False):
        """ Returns a list of node id's connecting the two nodes.
        """
        try: return proximity.dijkstra_shortest_path(self, id1, id2, heuristic, directed)
        except:
            return None
            
    def betweenness_centrality(self, normalized=True, directed=False):
        """ Calculates betweenness centrality and returns an node id -> weight dictionary.
        Node betweenness weights are updated in the process.
        """
        bc = proximity.brandes_betweenness_centrality(self, normalized, directed)
        for id, w in bc.iteritems(): self[id]._betweenness = w
        return bc
        
    def eigenvector_centrality(self, normalized=True, reversed=True, rating={},
                               start=None, iterations=100, tolerance=0.0001):
        """ Calculates eigenvector centrality and returns an node id -> weight dictionary.
        Node eigenvalue weights are updated in the process.
        """
        ec = proximity.eigenvector_centrality(
            self, normalized, reversed, rating, start, iterations, tolerance
        )
        for id, w in ec.iteritems(): self[id]._eigenvalue = w
        return ec
    
    def nodes_by_betweenness(self, treshold=0.0):
        """ Returns nodes sorted by betweenness centrality.
        Nodes with a lot of passing traffic will be at the front of the list.
        """
        nodes = [(n.betweenness, n) for n in self.nodes if n.betweenness > treshold]
        nodes.sort(); nodes.reverse()
        return [n for w, n in nodes]
        
    nodes_by_traffic = nodes_by_betweenness
    
    def nodes_by_eigenvalue(self, treshold=0.0):
        """ Returns nodes sorted by eigenvector centrality.
        Nodes with a lot of incoming traffic will be at the front of the list
        """
        nodes = [(n.eigenvalue, n) for n in self.nodes if n.eigenvalue > treshold]
        nodes.sort(); nodes.reverse()
        return [n for w, n in nodes]
        
    nodes_by_weight = nodes_by_eigenvalue
    
    def nodes_by_category(self, category):
        """ Returns nodes with the given category attribute.
        """
        return [n for n in self.nodes if n.category == category]

    def _leaves(self):
        """ Returns a list of nodes that have only one connection.
        """
        return [node for node in self.nodes if node.is_leaf]
        
    leaves = property(_leaves)
    
    def crown(self, depth=2):
        """ Returns a list of leaves, nodes connected to leaves, etc.
        """
        nodes = []
        for node in self.leaves: nodes += node.flatten(depth-1)
        return cluster.unique(nodes)
        
    fringe = crown
    
    def _density(self):
        """ The number of edges in relation to the total number of possible edges.
        """
        return 2.0*len(self.edges) / (len(self.nodes) * (len(self.nodes)-1))

    density = property(_density)
    
    def _is_complete(self) : return self.density == 1.0    
    def _is_dense(self)    : return self.density > 0.65
    def _is_sparse(self)   : return self.density < 0.35

    is_complete = property(_is_complete)
    is_dense    = property(_is_dense)
    is_sparse   = property(_is_sparse)
    
    def sub(self, id, distance=1):
        return cluster.subgraph(self, id, distance)
        
    subgraph = sub
        
    def __and__(self, graph):
        nodes = cluster.intersection(cluster.flatten(self), cluster.flatten(graph))
        all = self | graph
        return cluster.subgraph(all, nodes, 0)

    intersect = __and__

    def __or__(self, graph):
        g = self.copy()
        for n in graph.nodes:
            root = (g.root==None and graph.root==n)
            g.add_node(n.id, n.r, n.style, n.category, n.label, root, n.__dict__)
        for e in graph.edges:
            g.add_edge(e.node1.id, e.node2.id, e.weight, e.length, e.label, e.__dict__)
        return g

    join = __or__

    def __sub__(self, graph):
        nodes = cluster.difference(cluster.flatten(self), cluster.flatten(graph))
        all = self | graph
        return cluster.subgraph(all, nodes, 0)

    subtract = __sub__
    
    def _is_clique(self):
        return cluster.is_clique(self)
    is_clique = property(_is_clique)
    
    def clique(self, id, distance=0):
        return cluster.subgraph(self, cluster.clique(self, id), distance)
    
    def cliques(self, threshold=3, distance=0):
        g = []
        c = cluster.cliques(self, threshold)
        for nodes in c: g.append(cluster.subgraph(self, nodes, distance))
        return g
        
    def split(self):
        return cluster.partition(self)

### DYNAMIC GRAPH ####################################################################################

class xgraph(graph):
    
    """ A dynamic graph where a clicked node loads new data.
    
    Nodes are clickable and will load a new graph based on
    the following methods (that need to be subclassed or monkey patched):
    1) has_node(id): returns True when the id is a node in the dataset.
    2) get_links(id): a list of (weight, id) tuples directly connected to the node
    3) get_cluster(id): a list of (weight, id, [links]) tuples of node id's that are
       connected to the given node via the node id's in the links list (distance 2).   

    The idea is that you have a dataset stored in files or a database,
    and use the dynamic graph's method to describe how the data is read
    and interlinked. The graph is then automatically kept up to date
    as you browse through the connected nodes.
    
    """
    
    def __init__(self, iterations=500, distance=1.0, layout=LAYOUT_SPRING):
        
        graph.__init__(self, iterations, distance, layout)
        self.styles = create().styles
        self.events.click = self.click
        self.max = 20
        
        self._dx = 0
        self._dy = 0
    
    def has_node(self, id):
        return True
    
    def get_links(self, id):    
        return []
        
    def get_cluster(self, id):
        return []
    
    def load(self, id):
        
        """ Rebuilds the graph around the given node id.
        """
        
        self.clear()
    
        # Root node.
        self.add_node(id, root=True)
    
        # Directly connected nodes have priority.
        for w, id2 in self.get_links(id):
            self.add_edge(id, id2, weight=w)
            if len(self) > self.max: 
                break

        # Now get all the other nodes in the cluster.
        for w, id2, links in self.get_cluster(id):
            for id3 in links:
                self.add_edge(id3, id2, weight=w)
                self.add_edge(id, id3, weight=w)
            #if len(links) == 0:
            #    self.add_edge(id, id2)
            if len(self) > self.max: 
                break    

        # Provide a backlink to the previous root.
        if self.event.clicked: 
            g.add_node(self.event.clicked)
        
    def click(self, node):
        
        """ Callback from graph.events when a node is clicked.
        """
        
        if not self.has_node(node.id): return
        if node == self.root: return
        
        self._dx, self._dy = self.offset(node)
        self.previous = self.root.id
        self.load(node.id)  
            
    def draw(self, weighted=False, directed=False, highlight=[], traffic=None):
        
        # A new graph unfolds from the position of the clicked node.
        graph.draw(self, self._dx, self._dy, 
            weighted, directed, highlight, traffic
        )
        self._dx *= 0.9
        self._dy *= 0.9

#### COMMANDS ########################################################################################

def create(iterations=1000, distance=1.0, layout=LAYOUT_SPRING, depth=True):
    
    """ Returns a new graph with predefined styling.
    """

    global _ctx
    try:
        from nodebox.graphics import RGB
        _ctx.colormode(RGB)
        g = graph(iterations, distance, layout)
    except:
        _ctx = None
        g = graph(iterations, distance, layout)
        return g
    
    # Styles for different types of nodes.
    s = style.style
    g.styles.append(s(style.LIGHT    , _ctx, fill   = _ctx.color(0.0, 0.0, 0.0, 0.20)))
    g.styles.append(s(style.DARK     , _ctx, fill   = _ctx.color(0.3, 0.5, 0.7, 0.75)))
    g.styles.append(s(style.BACK     , _ctx, fill   = _ctx.color(0.5, 0.8, 0.0, 0.50)))
    g.styles.append(s(style.IMPORTANT, _ctx, fill   = _ctx.color(0.3, 0.6, 0.8, 0.75)))
    g.styles.append(s(style.HIGHLIGHT, _ctx, stroke = _ctx.color(1.0, 0.0, 0.5), strokewidth=1.5))
    g.styles.append(s(style.MARKED   , _ctx))
    g.styles.append(s(style.ROOT     , _ctx, text   = _ctx.color(1.0, 0.0, 0.4, 1.00), 
                                             stroke = _ctx.color(0.8, 0.8, 0.8, 0.60),
                                             strokewidth = 1.5, 
                                             fontsize    = 16, 
                                             textwidth   = 150))

    # Important nodes get a double stroke.
    def important_node(s, node, alpha=1.0):
        style.style(None, _ctx).node(s, node, alpha)
        r = node.r * 1.4
        _ctx.nofill()
        _ctx.oval(node.x-r, node.y-r, r*2, r*2)  

    # Marked nodes have an inner dot.
    def marked_node(s, node, alpha=1.0):
        style.style(None, _ctx).node(s, node, alpha)
        r = node.r * 0.3
        _ctx.fill(s.stroke)
        _ctx.oval(node.x-r, node.y-r, r*2, r*2)
    
    g.styles.important.node = important_node
    g.styles.marked.node = marked_node 
    
    g.styles.depth = depth

    # Styling guidelines. All nodes have the default style, except:
    # 1) a node directly connected to the root gets the LIGHT style.
    # 2) a node with more than 4 edges gets the DARK style.
    # 3) a node with a weight of 0.75-1.0 gets the IMPORTANT style.
    # 4) the graph.root node gets the ROOT style.
    # 5) the node last clicked gets the BACK style.    
    g.styles.guide.append(style.LIGHT     , lambda graph, node: graph.root in node.links)
    g.styles.guide.append(style.DARK      , lambda graph, node: len(node.links) > 4)
    g.styles.guide.append(style.IMPORTANT , lambda graph, node: node.weight > 0.75)
    g.styles.guide.append(style.ROOT      , lambda graph, node: node == graph.root)
    g.styles.guide.append(style.BACK      , lambda graph, node: node == graph.events.clicked)
    
    # An additional rule applies every node's weight to its radius.
    def balance(graph, node): 
        node.r = node.r*0.75 + node.r*node.weight*0.75
    g.styles.guide.append("balance", balance)
    
    # An additional rule that keeps leaf nodes closely clustered.
    def cluster(graph, node):
        if len(node.links) == 1: 
            node.links.edge(node.links[0]).length *= 0.5
    g.styles.guide.append("cluster", cluster)
    
    g.styles.guide.order = [
        style.LIGHT, style.DARK, style.IMPORTANT, style.ROOT, style.BACK, "balance", "nurse"
    ]

    return g

# 1.9.5.6
# Fixed circle_layout copy (number of orbits and starting angle weren't copied).

# 1.9.5.5
# graph.add_node and graph.add_edge call graph.new_node and graph.new_edge respectively.
# This should make subclassing nodes and edges a little easier.

# 1.9.5.4
# Fixex bug in spring_layout.tweak().
# Added directed=False parameter to dijkstra_shortest_path() and brandes_betweenness_centrality().

# 1.9.5.3
# Copies of nodes and edges correctly copy arbitrary attributes,
# e.g. edge.context, edge.relation and edge.author in a Perception graph.

# 1.9.5.2
# Reverted to old cluster.unique() (less fast but retains sort order).

# 1.9.5.1
# graph.draw() in push/pop.
# graph.node_id works like graph.node(id).
# Added graph.leaves property.
# Added graph.fringe() method.
# Added node.is_leaf property.
# Added node.can_reach().
# Added proximity.depth_first_search().
# graph.style.align supports RIGHT and CENTER.
# graph.layout.refresh() False rekindles the animation.
# import graph works outside NodeBox.

# 1.9.5
# Changed property names in spring_layout class.
# Added orbit property to circle_layout.
# Added force and repulsion properties to spring_layout.
# Increased default repulsion radius from 7 to 15.
# Added nurse behavior to the styleguide (edge length for leaves is 0.5).

# 1.9.4
# Edges now have a length property that controls individual attraction.

# 1.9.2.1
# proximity.eigenvector_centrality() yields warning 
# instead of exception if it does not converge.
# Added heuristic parameter to proximity.dijkstra_shortest_path().
# Added layout.spring_layout.tweak()
# Added cluster.partition()

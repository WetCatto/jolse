from .config import RoadNetworkDefault
from .vehicle import Vehicle

import networkx as nx
from math import sqrt

class RoadNetwork:
    """
    Describes the topology of the road network. It is assumed that the network 
    resides in a 2D space where distances are measured in meters (m).
    """
    
    def __init__(self):
        """Initializes an empty road network."""
        self.graph = nx.DiGraph()
        
    def add_node(self, node_id: int, pos: tuple[int,int], traffic_light = None) -> None:
        """
        Adds a node to the network. This usually represents an intersection,
        but generally can represent any relevant feature in the network.
        """
        if node_id in self.graph.nodes: raise ValueError('Node ID already exists.')
        self.graph.add_node(node_id, pos = pos, traffic_light = traffic_light)

    def add_road(self, start_node_id: int, end_node_id: int, 
                 num_lanes = RoadNetworkDefault.NUM_LANES, 
                 speed_limit = RoadNetworkDefault.SPEED_LIMIT) -> None: 
        """Adds a road between two nodes. Note that this generated road is one-way."""
        start_x, start_y = self.graph.nodes[start_node_id]['pos']
        end_x, end_y = self.graph.nodes[end_node_id]['pos']
        length = sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        if length <= 0: raise ValueError('Road length cannot be 0.')
        
        vehicles = {lane_id: [] for lane_id in range(num_lanes)}
        self.graph.add_edge(
            start_node_id, end_node_id,
            length = length, 
            num_lanes = num_lanes, 
            speed_limit = speed_limit, 
            vehicles = vehicles
        )

    def add_two_way_road(self, node_a_id: int, node_b_id: int, 
                         num_lanes = RoadNetworkDefault.NUM_LANES, 
                         speed_limit = RoadNetworkDefault.SPEED_LIMIT) -> None:
        """Convenience method to add two-way streets between two nodes."""
        self.add_road(node_a_id, node_b_id, num_lanes, speed_limit)
        self.add_road(node_b_id, node_a_id, num_lanes, speed_limit)


    def add_vehicle(self, vehicle: Vehicle, start_node_id: int, 
                    end_node_id: int, lane_index: int) -> None:
        """Adds a vehicle to the road network."""
        road = self.get_road(start_node_id, end_node_id)
        if lane_index < 0 or lane_index >= road['num_lanes']: 
            raise ValueError('Lane is non-existent')
        road['vehicles'][lane_index].append(vehicle)

    def get_road(self, start_node_id: int, end_node_id: int) -> dict: 
        """
        Gets the road between two nodes as a dictionary, which contains the
        given road's information.
        """
        if (start_node_id, end_node_id) not in self.graph.edges:
            raise ValueError('No road between the two nodes.')
        return self.graph.edges[start_node_id, end_node_id]

    def get_road_length(self, start_node_id: int, end_node_id: int) -> float:
        """Gets the length of the road between two nodes, if any exists"""
        return self.get_road(start_node_id, end_node_id)['length']
                    
    def get_shortest_route(self, start_node_id: int, end_node_id: int) -> list[tuple[int,int]]:
        """Gets the route between two nodes with the shortest distance."""
        path = nx.shortest_path(self.graph, start_node_id, end_node_id, weight = 'length')
        if not path: raise ValueError('No route between the two nodes.')
        return [(path[i], path[i+1]) for i in range(len(path)-1)]


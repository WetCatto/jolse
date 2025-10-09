from .config import IDMDefault, SimulationDefault, VehicleDefault
from .vehicle import Vehicle
from .road_network import RoadNetwork
from .traffic_light import LightState

from math import sqrt

class Simulation:
    """Manages the state and progression of the traffic simulation."""

    def __init__(self, road_network: RoadNetwork, dt = SimulationDefault.TIME_STEP): 
        """Takes in a road network and manages the state of the traffic simulation"""
        self.road_network = road_network 
        self.dt = dt

        self.time = 0.0
        self.vehicles = []
        self.completed_vehicles = []
        self.next_vehicle_id = 0 

    def step(self) -> None:
        """Performs a time step and updates the state of the simulation."""
        # Update all traffic lights
        self._update_traffic_lights()

        # Update the physics of all vehicles (IDM)
        for vehicle in self.vehicles:
            acc = self.compute_acceleration(vehicle)
            vehicle.set_acceleration(acc)
            vehicle.update(self.dt)

        # Handle vehicles that reached the end of the road
        for vehicle in self.vehicles[:]:
            road_length = self.road_network.get_road_length(*vehicle.current_road)
            if vehicle.position >= road_length: 
                if self._can_enter_intersection(vehicle):
                    self.handle_road_transition(vehicle)
                else:
                    vehicle.position = road_length - SimulationDefault.STOP_LINE_OFFSET
                    vehicle.speed = 0
                    vehicle.set_acceleration(0)

        # Increment time
        self.time += self.dt

    def spawn_vehicle(self, start_node_id: int, end_node_id: int, destination_node_id: int, 
                      lane_index: int, length = VehicleDefault.VEHICLE_LENGTH, 
                      max_speed = VehicleDefault.MAX_SPEED, 
                      desired_speed_factor = VehicleDefault.DESIRED_SPEED_FACTOR, 
                      min_gap = VehicleDefault.MIN_GAP, 
                      max_acceleration = VehicleDefault.MAX_ACCELERATION, 
                      max_deceleration = VehicleDefault.MAX_DECELERATION) -> None:
        """
        Spawns a vehicle on a given road segment, if it exists. The ID is
        automatically computed for each spawned vehicle.
        """
        road = self.road_network.get_road(start_node_id, end_node_id)
        route = self.road_network.get_shortest_route(start_node_id, destination_node_id)

        if lane_index < 0 or lane_index >= road['num_lanes']:
            raise ValueError('Lane is non-existent')

        v = Vehicle(self.next_vehicle_id, initial_road = (start_node_id, end_node_id), 
                    initial_lane = lane_index, initial_pos = 0, route = route, 
                    length = length, max_speed = max_speed, 
                    road_speed_limit = road['speed_limit'],
                    desired_speed_factor = desired_speed_factor, min_gap = min_gap,
                    max_acceleration = max_acceleration, 
                    max_deceleration = max_deceleration)

        self.vehicles.append(v)
        self.road_network.add_vehicle(v, start_node_id, end_node_id, lane_index)
        self.next_vehicle_id += 1
    
    def compute_acceleration(self, vehicle: Vehicle) -> float:
        """Computes the acceleration of the vehicle using the Intelligent Driver Model"""
        # Check for physical leading vehicle
        leading_vehicle = vehicle.get_leading_vehicle(self.road_network)
    
        # Check for traffic light
        virtual_leader_distance = self._check_traffic_light(vehicle)
    
        # Use closer of the two constraints
        if virtual_leader_distance is not None:
            if leading_vehicle is None:
                # Only traffic light ahead
                gap = virtual_leader_distance
                delta_v = vehicle.speed  # Virtual leader has 0 speed
                use_virtual = True
            else:
                # Both physical leader and traffic light
                physical_gap = leading_vehicle.position - vehicle.position - vehicle.length
                if virtual_leader_distance < physical_gap:
                    gap = virtual_leader_distance
                    delta_v = vehicle.speed
                    use_virtual = True
                else:
                    gap = physical_gap
                    delta_v = vehicle.speed - leading_vehicle.speed
                    use_virtual = False
        else:
        # No traffic light constraint
            if leading_vehicle is None:
                # Free flow
                T = IDMDefault.TIME_HEADWAY
                delta = IDMDefault.DELTA
                free_flow_term = 1 - (vehicle.speed / vehicle.desired_speed) ** delta
                return vehicle.max_acceleration * free_flow_term
            else:
                gap = leading_vehicle.position - vehicle.position - vehicle.length
                delta_v = vehicle.speed - leading_vehicle.speed
                use_virtual = False
    
        # IDM calculation
        T = IDMDefault.TIME_HEADWAY
        delta = IDMDefault.DELTA
    
        free_flow_term = 1 - (vehicle.speed / vehicle.desired_speed) ** delta
    
        s_star = (vehicle.min_gap + vehicle.speed * T +
                 (vehicle.speed * delta_v) / (2 * sqrt(vehicle.max_acceleration * vehicle.max_deceleration)))
    
        interaction_term = (s_star / max(gap, 0.1)) ** 2
        return vehicle.max_acceleration * (free_flow_term - interaction_term)

    def handle_road_transition(self, vehicle: Vehicle) -> None:
        """
        Handles vehicle transitions in the network, whether they should be moved
        to the next road in their route, or removed if they are finished.
        """
        # Remove vehicle from its old road
        current_road_tuple = vehicle.current_road
        overshoot = vehicle.position - self.road_network.get_road_length(*current_road_tuple)
        old_road = self.road_network.get_road(*current_road_tuple)
        old_road['vehicles'][vehicle.current_lane].remove(vehicle)
        vehicle.route_index += 1
        
        # If the route is finished, remove the vehicle from simulation
        if vehicle.route_index >= len(vehicle.route):
            self.remove_vehicle(vehicle)
            return

        # Otherwise, place it on the next road in its route
        vehicle.position = max(0, overshoot)
        vehicle.current_road = vehicle.route[vehicle.route_index]
        new_road = self.road_network.get_road(*vehicle.current_road)
        
        # Simple logic to handle lane changes if new road has fewer lanes
        if vehicle.current_lane >= new_road['num_lanes']:
            vehicle.current_lane = new_road['num_lanes'] - 1

        new_road['vehicles'][vehicle.current_lane].append(vehicle)

    def remove_vehicle(self, vehicle: Vehicle) -> None:
        """
        Removes the vehicle from the road network, after completing their route.
        """
        # Remove from the road it's currently on
        road = self.road_network.get_road(*vehicle.current_road)
        if vehicle in road['vehicles'][vehicle.current_lane]:
            road['vehicles'][vehicle.current_lane].remove(vehicle)
        
        # Remove from the main simulation list and archive it
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            self.completed_vehicles.append(vehicle)

    def _check_traffic_light(self, vehicle: Vehicle) -> float:
        """
        Check if vehicle is approaching a red/yellow light. 
        Returns the distance from the vehicle to the stop light, if one exists
        """
        # Get current road info
        road_length = self.road_network.get_road_length(*vehicle.current_road)
        distance_to_end = road_length - vehicle.position
    
        # Only check if close to intersection
        if distance_to_end > VehicleDefault.INTERSECTION_DETECTION_DISTANCE:
            return None
    
        # Get intersection node
        _, end_node_id = vehicle.current_road
        node_data = self.road_network.graph.nodes[end_node_id]
        traffic_light = node_data.get('traffic_light')
        if traffic_light is None: return None # No light at this intersection
    
        # Check light state for this road
        light_state = traffic_light.get_state_for_road(*vehicle.current_road)
        if light_state == LightState.GREEN: return None  # Can proceed
    
        # Red or Yellow - need to stop
        # Return distance to stop line (slightly before intersection)
        stop_line_distance = distance_to_end - SimulationDefault.STOP_LINE_OFFSET 
        return max(stop_line_distance, SimulationDefault.STOP_LINE_OFFSET)

    def _update_traffic_lights(self) -> None:
        """Update all traffic lights in the network"""
        for node_id, node_data in self.road_network.graph.nodes(data=True):
            traffic_light = node_data.get('traffic_light')
            if traffic_light is not None:
                traffic_light.update(self.dt)

    def _can_enter_intersection(self, vehicle: Vehicle) -> bool:
        """Check if vehicle can proceed through intersection."""
        # Get intersection node
        _, end_node_id = vehicle.current_road
        node_data = self.road_network.graph.nodes[end_node_id]
        traffic_light = node_data.get('traffic_light')
    
        if traffic_light is None: return True
    
        # Check light state
        light_state = traffic_light.get_state_for_road(*vehicle.current_road)
        return light_state == LightState.GREEN
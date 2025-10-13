from .config import IDMDefault, SimulationDefault, VehicleDefault
from .vehicle import Vehicle
from .road_network import RoadNetwork
from .traffic_light import LightState
from .vehicle_profile import VehicleProfile
from .demand_pattern import DemandPattern

import math
import random

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

        self.traffic_enabled = False
        self.demand_pattern = None
        self.time_until_next_spawn = 0.0
        self.origin_destination_pairs = []
        self.spawn_points = []
        self.vehicle_profiles = VehicleProfile.get_all_profiles()

    def step(self) -> None:
        """Performs a time step and updates the state of the simulation."""
        # Update traffic generation
        if self.traffic_enabled:
            self._update_traffic_generation()

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
            stop_line_position = road_length - SimulationDefault.STOP_LINE_OFFSET

            if vehicle.position >= stop_line_position:
                if self._can_enter_intersection(vehicle):
                    if vehicle.position >= road_length:
                        self.handle_road_transition(vehicle)
                else:
                    vehicle.position = stop_line_position
                    vehicle.speed = 0
                    vehicle.set_acceleration(0)

        # Increment time
        self.time += self.dt
    
    def enable_traffic_generation(self, demand_pattern=DemandPattern.create_constant_pattern()):
        """Enables automatic traffic generation."""
        self.demand_pattern = demand_pattern
        self.traffic_enabled = True
        self.time_until_next_spawn = 0.0

    def disable_traffic_generation(self):
        """Disables automatic traffic generation."""
        self.traffic_enabled = False

    def add_origin_destination_pair(self, origin: int, destination: int, weight = 1.0):
        """Adds an origin-destination pair for traffic generation"""
        self.origin_destination_pairs.append((origin, destination, weight))
    
    def add_spawn_point(self, node_id: int, outgoing_node_id: int):
        """Adds a spawn point where vehicles enter the simulation."""
        self.spawn_points.append((node_id, outgoing_node_id))

    def spawn_vehicle(self, start_node_id: int, end_node_id: int, destination_node_id: int, 
                      lane_index: int, length = VehicleDefault.VEHICLE_LENGTH, 
                      max_speed = VehicleDefault.MAX_SPEED, 
                      desired_speed_factor = VehicleDefault.DESIRED_SPEED_FACTOR, 
                      min_gap = VehicleDefault.MIN_GAP, time_headway = IDMDefault.TIME_HEADWAY,
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
                    time_headway = time_headway,
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
            else:
                # Both physical leader and traffic light
                physical_gap = leading_vehicle.position - vehicle.position - vehicle.length
                if virtual_leader_distance < physical_gap:
                    gap = virtual_leader_distance
                    delta_v = vehicle.speed
                else:
                    gap = physical_gap
                    delta_v = vehicle.speed - leading_vehicle.speed
        else:
        # No traffic light constraint
            if leading_vehicle is None:
                # Free flow
                T = vehicle.time_headway
                delta = IDMDefault.DELTA
                free_flow_term = 1 - (vehicle.speed / vehicle.desired_speed) ** delta
                return vehicle.max_acceleration * free_flow_term
            else:
                gap = leading_vehicle.position - vehicle.position - vehicle.length
                delta_v = vehicle.speed - leading_vehicle.speed
    
        # IDM calculation
        T = vehicle.time_headway
        delta = IDMDefault.DELTA
    
        free_flow_term = 1 - (vehicle.speed / vehicle.desired_speed) ** delta
    
        s_star = (vehicle.min_gap + vehicle.speed * T +
                 (vehicle.speed * delta_v) / (2 * math.sqrt(vehicle.max_acceleration * vehicle.max_deceleration)))
    
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

    def _update_traffic_generation(self) -> None:
        """Automatically spawns vehicles based on the demand pattern."""
        if not self.demand_pattern: return

        current_spawn_rate = self.demand_pattern.get_spawn_rate(self.time)
        if current_spawn_rate <= 0: return

        self.time_until_next_spawn -= self.dt

        while self.time_until_next_spawn <= 0:
            self._spawn_traffic_vehicle()
            self.time_until_next_spawn += self._sample_spawn_time(current_spawn_rate)
        
    def _spawn_traffic_vehicle(self):
        """Spawn a single vehicle with a random profile."""
        if not self.origin_destination_pairs or not self.spawn_points: return

        od_pair = self._select_od_pair()
        if od_pair is None: return 
        origin, destination, _ = od_pair 

        valid_spawn_points = [
            (node, out_node) for node, out_node in self.spawn_points if node == origin
        ]
        if not valid_spawn_points: return 

        start_node, next_node = random.choice(valid_spawn_points)
        road = self.road_network.get_road(start_node, next_node)
        lane = random.randint(0, road['num_lanes'] - 1)
        if not self._is_spawn_location_clear(start_node, next_node, lane): return 

        _, profile = VehicleProfile.select_vehicle()
        try:
            self.spawn_vehicle(
                start_node, next_node, destination, lane,
                length = profile['length'], max_speed = profile['max_speed'],
                desired_speed_factor = random.uniform(*profile['desired_speed_factor']),
                max_acceleration = profile['max_acceleration'],
                max_deceleration = profile['max_deceleration'],
                time_headway = profile['time_headway'],
            )
        except Exception:
            pass

    def _sample_spawn_time(self, spawn_rate: float) -> float:
        """Select the next time until next spawn. Follows an exponential distribution"""
        if spawn_rate <= 0: return float('inf')
        return -1.0 / spawn_rate * math.log(random.random())

    def _select_od_pair(self):
        if not self.origin_destination_pairs: return None

        total_weight = sum(weight for _, _, weight in self.origin_destination_pairs)
        r = random.uniform(0, total_weight)

        cumulative = 0
        for od_pair in self.origin_destination_pairs:
            origin, dest, weight = od_pair
            cumulative += weight
            if r <= cumulative:
                return od_pair
        
        return self.od_pairs[-1]

    def _is_spawn_location_clear(self, start_node: int, next_node: int, lane: int,
                                 min_clearance = SimulationDefault.MIN_CLEARANCE):
        """Checks if the spawn location has enough clearance to spawn a vehicle."""
        road = self.road_network.get_road(start_node, next_node)
        vehicles_in_lane = road['vehicles'][lane]

        for vehicle in vehicles_in_lane:
            if vehicle.position < min_clearance: return False

        return True

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
        return max(stop_line_distance, 0.0)

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
from .config import IDMDefault, VehicleDefault

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .road_network import RoadNetwork

class Vehicle:
    """Describes a vehicle in the road network."""

    def __init__(self, vehicle_id: int, initial_road: tuple[int,int], 
                 initial_lane: int, initial_pos: float, route: list[tuple[int,int]], 
                 road_speed_limit: float, length = VehicleDefault.VEHICLE_LENGTH, 
                 max_speed = VehicleDefault.MAX_SPEED, 
                 desired_speed_factor = VehicleDefault.DESIRED_SPEED_FACTOR, 
                 max_acceleration = VehicleDefault.MAX_ACCELERATION, 
                 max_deceleration = VehicleDefault.MAX_DECELERATION,
                 time_headway = IDMDefault.TIME_HEADWAY, 
                 min_gap = VehicleDefault.MIN_GAP):
        """Constructs a vehicle on the given road and lane."""
        self.vehicle_id = vehicle_id
        self.length = length
        self.max_speed = max_speed
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.time_headway = time_headway
        self.min_gap = min_gap
        
        # Position and Routing
        self.current_road = initial_road 
        self.current_lane = initial_lane
        self.position = initial_pos 
        self.route = route
        self.route_index = 0
        
        # Physics
        self.desired_speed = road_speed_limit * desired_speed_factor 
        self.speed = 0 
        self.acceleration = 0
        self.previous_speed = 0 

        # Useful metrics
        self.total_wait_time = 0
        self.total_stops = 0
        self.time_alive = 0

    def update(self, dt: float) -> None:
        """Updates the vehicle's state on a given time step."""
        # Threshold considered to be stopping speed
        stop_threshold = VehicleDefault.STOP_THRESHOLD
        
        # Update physics
        self.speed += self.acceleration * dt 
        self.speed = max(0, min(self.speed, self.max_speed)) 
        self.position += self.speed * dt

        # Update metrics
        if self.speed < 1: self.total_wait_time += dt 
        if self.previous_speed > stop_threshold and self.speed <= stop_threshold:
            self.total_stops += 1
        self.time_alive += dt

        # Update previous velocity
        self.previous_speed = self.speed 

    def set_acceleration(self, acc: float) -> None:
        """Sets the vehicle's acceleration."""
        self.acceleration = max(-self.max_deceleration, min(acc, self.max_acceleration))

    def get_leading_vehicle(self, road_network: "RoadNetwork") -> "Vehicle":
        """Gets the leading vehicle in the lane."""
        road = road_network.get_road(*self.current_road)
        vehicles_in_lane = road['vehicles'][self.current_lane]

        # Sort vehicles by position to reliably find the leader
        vehicles_in_lane.sort(key=lambda v: v.position) 

        for v in vehicles_in_lane:
            if v.position > self.position:
                return v
        return None
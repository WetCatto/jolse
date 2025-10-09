from .config import TrafficLightDefault

from enum import IntEnum

class LightState(IntEnum):
    """Dictates the current state of the traffic light"""
    RED = 0
    YELLOW = 1
    GREEN = 2

    def __str__(self): return self.name

class Phase:
    """Represents a traffic light phase configuration."""

    def __init__(self, green_roads: list[tuple[int,int]], name: str = None):
        self.green_roads = set(green_roads)
        self.name = name or f'Phase-{id(self)}'

    def is_green(self, start_node_id: int, end_node_id: int) -> bool:
        """Checks if a given road has green light in this phase"""
        return (start_node_id, end_node_id) in self.green_roads

class TrafficLight:
    """Controls traffic flow at an intersection"""

    def __init__(self, intersection_id: int, phases: list[Phase],
                 green_time = TrafficLightDefault.GREEN_TIME,
                 yellow_time = TrafficLightDefault.YELLOW_TIME,
                 min_green_time = TrafficLightDefault.MIN_GREEN_TIME):
        self.intersection_id = intersection_id
        self.phases = phases 
        self.green_time = green_time
        self.min_green_time = min_green_time
        self.yellow_time = yellow_time
        
        # State
        self.current_phase_index = 0
        self.time_in_phase = 0.0
        self.state = LightState.GREEN 

        # Transition Checking
        self.transitioning = False
        self.next_phase_index = None
    
    @property
    def current_phase(self) -> Phase:
        """Gets the current phase of the traffic light."""
        return self.phases[self.current_phase_index]
        
    def update(self, dt: float) -> None:
        """
        Updates the traffic light for a given time step, and handles
        any necessary state transitions
        """
        self.time_in_phase += dt 

        if self.transitioning and self.state == LightState.YELLOW:
            if self.time_in_phase >= self.yellow_time:
                self.current_phase_index = self.next_phase_index
                self.state = LightState.GREEN
                self.time_in_phase = 0.0
                self.transitioning = False
                self.next_phase_index = None
        
    def can_change_phase(self) -> bool:
        """
        Checks if the traffic light can change phase. This is true if
        the light is not transitioning, and it has remained green for a given
        minimum duration.
        """
        if self.transitioning: return False 
        if self.state != LightState.GREEN: return False
        return self.time_in_phase >= self.min_green_time
    
    def request_phase_change(self, new_phase_index: int) -> bool:
        """Requests the traffic light to switch phases, if possible."""
        # Validate 
        if new_phase_index < 0 or new_phase_index >= len(self.phases):
            raise ValueError(f'Invalid phase index {new_phase_index}')

        if new_phase_index == self.current_phase_index: return False 
        if not self.can_change_phase(): return False

        # Initiate transition
        self.state = LightState.YELLOW
        self.transitioning = True 
        self.next_phase_index = new_phase_index
        self.time_in_phase = 0.0
        return True
    
    def get_state_for_road(self, start_node_id: int, end_node_id: int) -> LightState:
        """Gets the light state for a given road"""
        if self.state == LightState.YELLOW: return LightState.YELLOW

        if self.current_phase.is_green(start_node_id, end_node_id):
            return LightState.GREEN if self.state == LightState.GREEN else self.state
        else:
            return LightState.RED
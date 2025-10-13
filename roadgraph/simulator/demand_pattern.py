class DemandPattern:
    """Defines time-varying traffic demand patterns"""
    
    def __init__(self, name="default"):
        self.name = name
        self.time_periods = []  # List of (start_time, end_time, spawn_rate)
    
    def add_period(self, start_time, end_time, spawn_rate):
        """
        Add a time period with a specific spawn rate.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            spawn_rate: Vehicles per second during this period
        """
        self.time_periods.append((start_time, end_time, spawn_rate))
    
    def get_spawn_rate(self, current_time):
        """Get the spawn rate for the current simulation time"""
        for start, end, rate in self.time_periods:
            if start <= current_time < end:
                return rate
        
        # Default to 0 if no period matches
        return 0.0
    
    @staticmethod
    def create_rush_hour_pattern():
        """
        Create a typical rush hour pattern:
        - Low traffic: 0-300s (0.2 veh/s)
        - Morning rush: 300-600s (1.5 veh/s)
        - Midday: 600-900s (0.5 veh/s)
        - Evening rush: 900-1200s (1.5 veh/s)
        - Night: 1200s+ (0.2 veh/s)
        """
        pattern = DemandPattern("rush_hour")
        pattern.add_period(0, 300, 0.2)
        pattern.add_period(300, 600, 1.5)
        pattern.add_period(600, 900, 0.5)
        pattern.add_period(900, 1200, 1.5)
        pattern.add_period(1200, float('inf'), 0.2)
        return pattern
    
    @staticmethod
    def create_constant_pattern(spawn_rate=0.5):
        """Create a constant demand pattern"""
        pattern = DemandPattern("constant")
        pattern.add_period(0, float('inf'), spawn_rate)
        return pattern
    
    @staticmethod
    def create_heavy_traffic_pattern(spawn_rate=2.0):
        """Create constant heavy traffic"""
        pattern = DemandPattern("heavy")
        pattern.add_period(0, float('inf'), spawn_rate)
        return pattern
import random 

class VehicleProfile:
    """Defines different types of vehicles with varying characteristics."""

    CAR = {
        'length': 5.0,
        'max_speed': 40.0,
        'desired_speed_factor': (0.9, 1.0),
        'max_acceleration': 3.0,
        'max_deceleration': 5.0,
        'time_headway': 1.5,
        'weight': 0.5
    }

    AGGRESSIVE = {
        'length': 5.0,
        'max_speed': 45.0,
        'desired_speed_factor': (1.1, 1.2),
        'max_acceleration': 4.0,
        'max_deceleration': 6.0,
        'time_headway': 0.8,
        'weight': 0.25
    }

    CAUTIOUS = {
        'length': 5.0,
        'max_speed': 35.0,
        'desired_speed_factor': (0.8, 0.9),
        'max_acceleration': 2.5,
        'max_deceleration': 5.0,
        'time_headway': 2.0,
        'weight': 0.25
    }

    @classmethod
    def get_all_profiles(cls):
        """Returns all defined profiles with their weights."""
        return [
            ('car', cls.CAR), 
            ('aggressive', cls.AGGRESSIVE), 
            ('cautious', cls.CAUTIOUS)
        ]
    
    @classmethod 
    def select_vehicle(cls):
        """Selects a vehicle from a given profile."""
        profiles = cls.get_all_profiles()
        total_weight = sum(profile['weight'] for _, profile in profiles)
        r = random.uniform(0, total_weight)

        cumulative = 0
        for name, profile in profiles:
            cumulative += profile['weight']
            if r <= cumulative: return name, profile
        
        return profiles[0]
"""
Default (internal) configuration for the simulation.

All physical quantities use SI units:
- Distance: meters (m)
- Time: seconds (s)
- Speed: meters per second (m/s)
- Acceleration: meters per second squared (m/s^2)
"""

# ============================================================================ #
# Road Network Parameters                                                      #
# ============================================================================ #

class RoadNetworkDefault:
    NUM_LANES = 2
    SPEED_LIMIT = 15.0

# ============================================================================ #
# Traffic Light Parameters                                                     #
# ============================================================================ #

class TrafficLightDefault:
    GREEN_TIME = 30.0
    MIN_GREEN_TIME = 5.0
    YELLOW_TIME = 3.0

# ============================================================================ #
# Vehicle Parameters                                                           #
# ============================================================================ #

class VehicleDefault:
    VEHICLE_LENGTH = 5.0
    MAX_SPEED = 40.0
    DESIRED_SPEED_FACTOR = 1.0

    MAX_ACCELERATION = 3.0
    MAX_DECELERATION = 5.0

    MIN_GAP = 2.0
    STOP_THRESHOLD = 0.2

    INTERSECTION_DETECTION_DISTANCE = 20

# ============================================================================ #
# Simulation Parameters                                                        #
# ============================================================================ #

class SimulationDefault:
    TIME_STEP = 0.1
    STOP_LINE_OFFSET = 2.0
    MIN_CLEARANCE = 15.0

# ============================================================================ #
# Intelligent Driver Model (IDM) Parameters                                    #
# ============================================================================ #

class IDMDefault:
    TIME_HEADWAY = 1.5
    DELTA = 4.0
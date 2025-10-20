import time
from roadgraph.simulator import *

# Simulation parameters
ROAD_LENGTH = 100  # Distance from center to outer nodes
CENTER_X = 100
CENTER_Y = 100
SPAWN_RATE = 2.0  # Vehicles per second
LIGHT_DURATION = 30  # Seconds per phase
NUM_LANES = 2

def create_network():
    network = RoadNetwork()
    
    # Add nodes in a cross pattern
    network.add_node(1, (CENTER_X, CENTER_Y - ROAD_LENGTH))  # North
    network.add_node(2, (CENTER_X + ROAD_LENGTH, CENTER_Y))  # East
    network.add_node(3, (CENTER_X, CENTER_Y + ROAD_LENGTH))  # South
    network.add_node(4, (CENTER_X - ROAD_LENGTH, CENTER_Y))  # West
    network.add_node(5, (CENTER_X, CENTER_Y))  # Center
    
    # Add two-way roads
    for i in range(1, 5):
        network.add_two_way_road(i, 5, num_lanes=NUM_LANES)
    
    # Create and add traffic light
    phases = [
        Phase(green_roads=[(1,5), (3,5)], name='North-South'),
        Phase(green_roads=[(2,5), (4,5)], name='East-West'),
    ]
    light = TrafficLight(5, phases, green_time=LIGHT_DURATION)
    network.add_traffic_light(light)
    
    return network, light

def main():
    # Create network and initialize simulation
    network, light = create_network()
    sim = Simulation(network)
    viz = SimulationVisualizer(sim)
    
    # Setup traffic pattern
    pattern = DemandPattern.create_constant_pattern(SPAWN_RATE)
    sim.enable_traffic_generation(pattern)
    
    # Add spawn points
    for i in range(1, 5):
        sim.add_spawn_point(i, 5)
    
    # Add origin-destination pairs
    sim.add_origin_destination_pair(1, 3)  # North to South
    sim.add_origin_destination_pair(2, 4)  # East to West
    sim.add_origin_destination_pair(3, 1)  # South to North
    sim.add_origin_destination_pair(4, 2)  # West to East
    
    current_phase = 0
    last_phase_change = 0
    
    while True:
        try:
            # Update visualization
            viz.render(show_stats=True)
            
            # Check if it's time to change traffic light phase
            if sim.time - last_phase_change >= LIGHT_DURATION:
                next_phase = (current_phase + 1) % 2
                light.request_phase_change(next_phase)
                current_phase = next_phase
                last_phase_change = sim.time
            
            # Step simulation
            sim.step()
            
            # Wait to maintain 1 step per second
            time.sleep(1)
            
        except KeyboardInterrupt:
            print('Simulation terminated by user')
            viz.close()
            break

if __name__ == "__main__":
    main()

    






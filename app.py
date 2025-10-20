import streamlit as st
import matplotlib.pyplot as plt
from roadgraph.simulator import *
import time

def create_road_network(junction_radius, road_length, num_lanes=2):
    network = RoadNetwork()
    
    # Calculate positions based on parameters
    center_x, center_y = 100, 100
    node_positions = {
        1: (center_x, center_y - road_length),  # North
        2: (center_x + road_length, center_y),  # East
        3: (center_x, center_y + road_length),  # South
        4: (center_x - road_length, center_y),  # West
        5: (center_x, center_y)  # Center
    }
    
    # Add nodes
    for node_id, pos in node_positions.items():
        network.add_node(node_id, pos)
    
    # Add roads
    for i in range(1, 5):
        network.add_two_way_road(i, 5, num_lanes=num_lanes)
    
    return network

def main():
    st.title("Road Network Traffic Simulation")
    
    # Sidebar controls
    st.sidebar.header("Simulation Parameters")
    
    # Network parameters
    st.sidebar.subheader("Network Configuration")
    junction_radius = st.sidebar.slider("Junction Radius", 20, 100, 50)
    road_length = st.sidebar.slider("Road Length", 50, 200, 100)
    
    # Traffic parameters
    st.sidebar.subheader("Traffic Configuration")
    spawn_rate = st.sidebar.number_input("Vehicle Spawn Rate (vehicles/sec)", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
    traffic_light_duration = st.sidebar.number_input("Traffic Light Duration (sec)", min_value=10, max_value=120, value=30, step=5)
    num_lanes = st.sidebar.number_input("Number of Lanes per Road", min_value=1, max_value=4, value=2)
    
    # Vehicle Parameters
    st.sidebar.subheader("Vehicle Parameters")
    max_speed = st.sidebar.number_input("Max Vehicle Speed (m/s)", min_value=10.0, max_value=60.0, value=40.0, step=5.0)
    vehicle_length = st.sidebar.number_input("Vehicle Length (m)", min_value=3.0, max_value=10.0, value=5.0, step=0.5)
    time_headway = st.sidebar.number_input("Time Headway (s)", min_value=0.5, max_value=3.0, value=1.5, step=0.1)
    
    # Create network
    network = RoadNetwork()
    
    # Add nodes in a cross pattern
    center_x, center_y = 100, 100
    node_positions = {
        1: (center_x, center_y - road_length),  # North
        2: (center_x + road_length, center_y),  # East
        3: (center_x, center_y + road_length),  # South
        4: (center_x - road_length, center_y),  # West
        5: (center_x, center_y)  # Center
    }
    
    # Add nodes
    for node_id, pos in node_positions.items():
        network.add_node(node_id, pos)
    
    # Add roads
    for i in range(1, 5):
        network.add_two_way_road(i, 5, num_lanes=num_lanes)
    
    # Setup traffic lights
    phases = [
        Phase(green_roads=[(1,5), (3,5)], name='North-South'),
        Phase(green_roads=[(2,5), (4,5)], name='East-West'),
    ]
    light = TrafficLight(5, phases, green_time=traffic_light_duration)
    network.add_traffic_light(light)
    
    # Setup simulation
    sim = Simulation(network)
    viz = SimulationVisualizer(sim)
    
    # Create a custom vehicle profile
    custom_profile = {
        'length': vehicle_length,
        'max_speed': max_speed,
        'desired_speed_factor': (0.9, 1.0),
        'max_acceleration': 3.0,
        'max_deceleration': 5.0,
        'time_headway': time_headway,
        'weight': 1.0
    }
    
    # Configure traffic generation
    pattern = DemandPattern.create_constant_pattern(spawn_rate)
    sim.enable_traffic_generation(pattern)
    
    # Add spawn points
    for i in range(1, 5):
        sim.add_spawn_point(i, 5)
        
    # Add origin-destination pairs with parameters
    od_pairs = [(1, 3), (3, 1), (2, 4), (4, 2)]  # N-S, S-N, E-W, W-E
    for start, end in od_pairs:
        sim.add_origin_destination_pair(start, end, weight=1.0)
        
        # Add vehicles with custom profile when spawning
        road = network.get_road(start, 5)
        lane = 0
        sim.spawn_vehicle(
            start, 5, end, lane,
            length=custom_profile['length'],
            max_speed=custom_profile['max_speed'],
            desired_speed_factor=custom_profile['desired_speed_factor'][0],
            time_headway=custom_profile['time_headway']
        )

    # Main simulation control
    if 'running' not in st.session_state:
        st.session_state.running = False
    
    start_stop = st.button('Start/Stop Simulation')
    if start_stop:
        st.session_state.running = not st.session_state.running
    
    # Display area for the simulation
    viz_placeholder = st.empty()
    stats_container = st.container()
    
    with stats_container:
        stats_col1, stats_col2, stats_col3 = st.columns(3)
    
    current_phase = 0
    last_phase_change = 0
    last_update = time.time()
    
    try:
        while st.session_state.running:
            current_time = time.time()
            
            # Only update if 1 second has passed
            if current_time - last_update >= 1.0:
                # Check if it's time to change traffic light phase
                if sim.time - last_phase_change >= traffic_light_duration:
                    next_phase = (current_phase + 1) % 2
                    light.request_phase_change(next_phase)
                    current_phase = next_phase
                    last_phase_change = sim.time
                
                # Update simulation
                sim.step()
                
                # Update visualization
                viz.render(show_stats=True)
                viz_placeholder.pyplot(viz.fig, clear_figure=False)
                
                # Update statistics
                with stats_col1:
                    st.metric("Active Vehicles", len(sim.vehicles))
                with stats_col2:
                    st.metric("Completed Trips", len(sim.completed_vehicles))
                with stats_col3:
                    st.metric("Current Time", f"{sim.time:.1f}s")
                
                last_update = current_time
            else:
                # Small sleep to prevent CPU overload
                time.sleep(0.1)
            
    except Exception as e:
        st.error(f"Simulation error: {str(e)}")
        
if __name__ == "__main__":
    main()
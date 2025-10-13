"""
Visualization module for the traffic simulation.
Provides a minimalist, schematic view of the simulation state.
"""

from .traffic_light import LightState

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

class SimulationVisualizer:
    """
    Visualizes the traffic simulation with a minimalist schematic style.
    """
    
    def __init__(self, simulation, figsize=(12, 8)):
        """
        Args:
            simulation: Simulation instance to visualize
            figsize: Figure size (width, height) in inches
        """
        self.simulation = simulation
        self.network = simulation.road_network
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_aspect('equal')
        self.ax.set_facecolor('#f8f8f8')  # Light gray background
        self.fig.patch.set_facecolor('white')
        
        # Calculate bounds for the network
        self._calculate_bounds()
        
        # Style settings
        self.node_size = 200
        self.road_width = 2
        self.vehicle_size = 4
        
        # Color scheme (minimalist)
        self.colors = {
            'road': '#d0d0d0',
            'node': '#505050',
            'light_green': '#4CAF50',
            'light_yellow': '#FFC107',
            'light_red': '#F44336',
            'vehicle_car': '#2196F3',
            'vehicle_truck': '#FF9800',
            'vehicle_aggressive': '#E91E63',
            'vehicle_conservative': '#9C27B0',
            'text': '#303030'
        }

        # Initialize dynamic elements
        self.vehicle_patches = []
        self.light_patches = {}
        self.text_elements = []
        
        # Draw static elements once
        self._draw_network()
        
        plt.tight_layout()
    
    def _calculate_bounds(self):
        """Calculate visualization bounds based on network"""
        positions = [data['pos'] for _, data in self.network.graph.nodes(data=True)]
        if not positions:
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            return
        
        xs, ys = zip(*positions)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Add padding
        padding = 30
        self.ax.set_xlim(min_x - padding, max_x + padding)
        self.ax.set_ylim(min_y - padding, max_y + padding)
        
        # Remove axis ticks for cleaner look
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Minimal border
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#e0e0e0')
            spine.set_linewidth(0.5)
    
    def _draw_network(self):
        """Draw roads and intersections (static elements)"""
        # Draw roads first (so they appear behind nodes)
        for (from_id, to_id), road_data in self.network.graph.edges.items():
            from_pos = self.network.graph.nodes[from_id]['pos']
            to_pos = self.network.graph.nodes[to_id]['pos']
            
            # Draw road as line
            self.ax.plot([from_pos[0], to_pos[0]], 
                        [from_pos[1], to_pos[1]], 
                        color=self.colors['road'], 
                        linewidth=self.road_width * road_data['num_lanes'],
                        zorder=1, solid_capstyle='round')
        
        # Draw nodes
        for node_id, node_data in self.network.graph.nodes(data=True):
            pos = node_data['pos']
            has_light = node_data.get('traffic_light') is not None
            
            # Node circle
            color = self.colors['node']
            circle = plt.Circle(pos, radius=5, color=color, zorder=3)
            self.ax.add_patch(circle)
            
            # If has traffic light, add a larger circle for the light indicator
            if has_light:
                light_circle = plt.Circle(pos, radius=8, 
                                        facecolor='none',
                                        edgecolor=self.colors['node'],
                                        linewidth=1.5, zorder=2)
                self.ax.add_patch(light_circle)
                self.light_patches[node_id] = light_circle
    
    def render(self, show_stats=True):
        """
        Render the current simulation state.
        
        Args:
            show_stats: Whether to show statistics overlay
        """
        # Clear previous dynamic elements
        for patch in self.vehicle_patches:
            patch.remove()
        self.vehicle_patches.clear()
        
        for text in self.text_elements:
            text.remove()
        self.text_elements.clear()
        
        # Update traffic lights
        self._draw_traffic_lights()
        
        # Draw vehicles
        self._draw_vehicles()
        
        # Draw statistics overlay
        if show_stats:
            self._draw_stats()
        
        # Refresh display
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)  # Small pause to update display
    
    def _draw_traffic_lights(self):
        """Update traffic light colors"""
        for node_id, light_patch in self.light_patches.items():
            node_data = self.network.graph.nodes[node_id]
            traffic_light = node_data.get('traffic_light')
            
            if traffic_light:
                state = traffic_light.state
                if state == LightState.GREEN:
                    color = self.colors['light_green']
                elif state == LightState.YELLOW:
                    color = self.colors['light_yellow']
                else:  # RED
                    color = self.colors['light_red']
                
                light_patch.set_edgecolor(color)
                light_patch.set_linewidth(2.5)
    
    def _draw_vehicles(self):
        """Draw all vehicles on their respective roads"""
        for vehicle in self.simulation.vehicles:
            # Get road geometry
            from_id, to_id = vehicle.current_road
            from_pos = self.network.graph.nodes[from_id]['pos']
            to_pos = self.network.graph.nodes[to_id]['pos']
            
            # Calculate vehicle position along road
            road_length = self.network.get_road_length(from_id, to_id)
            t = vehicle.position / road_length if road_length > 0 else 0
            t = min(max(t, 0), 1)  # Clamp to [0, 1]
            
            x = from_pos[0] + t * (to_pos[0] - from_pos[0])
            y = from_pos[1] + t * (to_pos[1] - from_pos[1])
            
            # Offset by lane (for multi-lane roads)
            road_data = self.network.get_road(from_id, to_id)
            num_lanes = road_data['num_lanes']
            if num_lanes > 1:
                # Calculate perpendicular offset
                dx = to_pos[0] - from_pos[0]
                dy = to_pos[1] - from_pos[1]
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    # Perpendicular vector
                    perp_x = -dy / length
                    perp_y = dx / length
                    
                    # Offset based on lane (center lanes around road center)
                    lane_offset = (vehicle.current_lane - (num_lanes - 1) / 2) * 3
                    x += perp_x * lane_offset
                    y += perp_y * lane_offset
            
            # Choose color based on vehicle type/behavior
            color = self._get_vehicle_color(vehicle)
            
            # Draw vehicle as circle (simple and clean)
            circle = plt.Circle((x, y), radius=self.vehicle_size/2, 
                              color=color, zorder=4, alpha=0.8)
            self.ax.add_patch(circle)
            self.vehicle_patches.append(circle)
    
    def _get_vehicle_color(self, vehicle):
        """Determine vehicle color based on characteristics"""
        # Color by time headway (best indicator of behavior)
        if vehicle.time_headway < 1.0:
            return self.colors['vehicle_aggressive']
        elif vehicle.time_headway > 2.0:
            return self.colors['vehicle_conservative']
        elif vehicle.length > 8.0:
            return self.colors['vehicle_truck']
        else:
            return self.colors['vehicle_car']
    
    def _draw_stats(self):
        """Draw statistics overlay"""
        stats_text = (
            f"Time: {self.simulation.time:.1f}s\n"
            f"Active: {len(self.simulation.vehicles)}\n"
            f"Completed: {len(self.simulation.completed_vehicles)}"
        )
        
        if self.simulation.traffic_enabled and self.simulation.demand_pattern:
            rate = self.simulation.demand_pattern.get_spawn_rate(self.simulation.time)
            stats_text += f"\nSpawn Rate: {rate:.2f}/s"
        
        # Position in top-left corner
        text = self.ax.text(0.02, 0.98, stats_text,
                          transform=self.ax.transAxes,
                          verticalalignment='top',
                          fontsize=10,
                          color=self.colors['text'],
                          bbox=dict(boxstyle='round', facecolor='white', 
                                  alpha=0.8, edgecolor='#e0e0e0'))
        self.text_elements.append(text)
    
    def show(self):
        """Display the visualization window (blocking)"""
        plt.show()
    
    def close(self):
        """Close the visualization window"""
        plt.close(self.fig)
    
    def save_frame(self, filename):
        """
        Save current frame as image.
        
        Args:
            filename: Path to save image (e.g., 'frame.png')
        """
        self.fig.savefig(filename, dpi=150, bbox_inches='tight', 
                        facecolor='white')
    
    def record_gif(self, duration, filename='simulation.gif', fps=10):
        """
        Record simulation as GIF.
        
        Args:
            duration: Duration to record in seconds
            filename: Output GIF filename
            fps: Frames per second for the GIF
        """
        frames_to_record = int(duration * fps)
        steps_per_frame = max(1, int(1.0 / (self.simulation.dt * fps)))
        
        print(f"Recording {duration}s at {fps} FPS ({frames_to_record} frames)...")
        
        writer = PillowWriter(fps=fps)
        with writer.saving(self.fig, filename, dpi=100):
            for i in range(frames_to_record):
                # Run simulation for multiple steps per frame
                for _ in range(steps_per_frame):
                    self.simulation.step()
                
                # Render and capture frame
                self.render(show_stats=True)
                writer.grab_frame()
                
                if (i + 1) % 10 == 0:
                    print(f"  Recorded {i + 1}/{frames_to_record} frames...")
        
        print(f"GIF saved to {filename}")
from roadgraph.simulator import *
test = RoadNetwork()

test.add_node(1, (100,0))
test.add_node(2, (200,100))
test.add_node(3, (100,200))
test.add_node(4, (0,100))
test.add_node(5, (100, 100))

test.add_two_way_road(1,5)
test.add_two_way_road(2,5)
test.add_two_way_road(3,5)
test.add_two_way_road(4,5)

phases = [
    Phase(green_roads = [(1,5), (3,5)], name = 'Road 1->5'),
    Phase(green_roads = [(2,5), (4,5)], name = 'Road 2->5'),
]
light = TrafficLight(5, phases)
test.add_traffic_light(light)

sim = Simulation(test)
viz = SimulationVisualizer(sim)

heavy_hour = DemandPattern.create_heavy_traffic_pattern(20)
sim.enable_traffic_generation(heavy_hour)
for i in range(1,5):
    sim.add_spawn_point(i,5)

sim.add_origin_destination_pair(1,3)
sim.add_origin_destination_pair(2,4)
sim.add_origin_destination_pair(3,1)
sim.add_origin_destination_pair(4,2)

current_phase = 0

i = 0
while True:
    try:
        if i % 30 == 0: viz.render(show_stats = True)
        if i % 60 == 0:
            next_phase = (current_phase + 1) % 2
            light.request_phase_change(next_phase)
            current_phase = next_phase

        sim.step()
    except KeyboardInterrupt:
        print('Terminating...')
        viz.close()
        exit()
    finally:
        i += 1

    






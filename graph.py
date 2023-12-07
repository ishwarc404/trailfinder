#Code which generates the relation graph

import json
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic


# Load data
with open('way_objects.json') as fp:
    way_objects = json.load(fp)

G = nx.DiGraph()

# Define a function to check if two points are within 10 meters
def is_within_distance(point1, point2, distance_m=10):
    return geodesic(point1, point2).meters <= distance_m

way_relations = {}
not_first_ways = [] #stores all the ways which are never first i.e children

# Create nodes for each way ID
for wayid in way_objects:
    way_relations[wayid] = []
    G.add_node(wayid)

# Create edges based on proximity
for wayid, coordinates in way_objects.items():
    end_point = tuple(coordinates[-1])
    for other_wayid, other_coordinates in way_objects.items():
        if wayid != other_wayid:
            start_point_other = tuple(other_coordinates[0])
            if is_within_distance(end_point, start_point_other):
                way_relations[wayid].append(other_wayid)
                not_first_ways.append(other_wayid)
                G.add_edge(wayid, other_wayid)

# Since way IDs are not geographical points, we use the spring layout for visualization
pos = nx.spring_layout(G)


# Visualize the graph
nx.draw(G, pos, with_labels=True, node_size=50)
# plt.show()



#lets get the list of ways which mark the beginning of the tree
all_ways = set(way_objects.keys())
not_first_ways = set(not_first_ways)
first_ways = all_ways - not_first_ways
print(len(all_ways))
print(len(not_first_ways))
print(len(first_ways)) 
first_way_objects = {x: way_objects[x] for x in way_objects.keys() if x  in first_ways}

with open('first_way_objects.json', 'w+') as fp:
    json.dump(first_way_objects, fp)



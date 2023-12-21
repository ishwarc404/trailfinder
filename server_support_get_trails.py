import json
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import folium
import polyline
import requests


# Load data
with open('way_objects.json') as fp:
    way_objects = json.load(fp)

with open('broken_way_objects.json') as fp:
    broken_way_objects = json.load(fp)

with open('way_metrics.json') as fp:
    way_metrics = json.load(fp)


# Define a function to check if two points are within 10 meters
def is_within_distance(point1, point2, distance_m=10):
    return geodesic(point1, point2).meters <= distance_m


def calculate_distance_elevation(wayid):
    """
    Calculate the total distance and elevation gain of a way.
    way_coordinates: List of (latitude, longitude) tuples.
    elevations: List of elevations corresponding to each coordinate.
    """
    total_distance = way_metrics[wayid]['distance']  # Total distance in meters
    total_elevation_gain = way_metrics[wayid]['gain']  # Total elevation gain in meters

    return [total_distance, total_elevation_gain]

def dfs_find_trails(G, start_node, target_distance, target_elevation_gain, current_path=None, current_distance=0, current_elevation=0, distance_tolerance=50, elevation_tolerance=100):
    if current_path is None:
        current_path = []

    # Add the start_node to the current path
    current_path.append(start_node)

    # Calculate the distance and elevation for the new way
    way_distance, way_elevation = calculate_distance_elevation(start_node)
    new_distance = current_distance + way_distance
    new_elevation = current_elevation + way_elevation

    # Check if the current path meets the distance and elevation criteria within the tolerances
    if new_distance >= target_distance - distance_tolerance and new_distance <= target_distance + distance_tolerance and new_elevation >= target_elevation_gain - elevation_tolerance and new_elevation <= target_elevation_gain + elevation_tolerance:
        return [current_path.copy()]  # Return a copy to avoid mutating the original list

    paths = []
    if new_distance <= target_distance + distance_tolerance and new_elevation <= target_elevation_gain + elevation_tolerance:
        for node in G.successors(start_node):
            # Check if the node has already been visited in the current path
            if node not in current_path:
                # Continue the search if the new distance and elevation are within tolerance
                sub_paths = dfs_find_trails(G, node, target_distance, target_elevation_gain, current_path.copy(), new_distance, new_elevation, distance_tolerance, elevation_tolerance)
                paths.extend(sub_paths)

    # No need to backtrack because we're working with a copy of the path
    return paths


def dfs_find_trails_in_range(G, start_node, min_distance, max_distance, min_elevation_gain, max_elevation_gain, current_path=None, current_distance=0, current_elevation=0, distance_tolerance=50, elevation_tolerance=100):

    if current_path is None:
        current_path = []

    # Add the start_node to the current path
    current_path.append(start_node)

    # Calculate the distance and elevation for the new way
    way_distance, way_elevation = calculate_distance_elevation(start_node)
    new_distance = current_distance + way_distance
    new_elevation = current_elevation + way_elevation

    # Check if the current path meets the distance and elevation criteria within the tolerances
    if (new_distance >= min_distance - distance_tolerance and new_distance <= max_distance + distance_tolerance and 
        new_elevation >= min_elevation_gain - elevation_tolerance and new_elevation <= max_elevation_gain + elevation_tolerance):
        return [current_path.copy()]  # Return a copy to avoid mutating the original list

    paths = []
    if (new_distance <= max_distance + distance_tolerance and 
        new_elevation <= max_elevation_gain + elevation_tolerance):
        for node in G.successors(start_node):
            # Check if the node has already been visited in the current path
            if node not in current_path:
                # Continue the search if the new distance and elevation are within tolerance
                sub_paths = dfs_find_trails_in_range(G, node, min_distance, max_distance, min_elevation_gain, max_elevation_gain, current_path.copy(), new_distance, new_elevation, distance_tolerance, elevation_tolerance)
                paths.extend(sub_paths)

    return paths


def get_distance_elevation(way_coordinates):
    total_distance = 0  # Total distance in meters
    total_elevation_gain = 0

    for i in range(len(way_coordinates) - 1):
        # Calculate distance between consecutive points
        point1 = way_coordinates[i]
        point2 = way_coordinates[i+1]

        distance = geodesic(point1, point2).meters
        total_distance += distance

    
    point1 = way_coordinates[0]
    point2 = way_coordinates[-1]


    point1_elevation = 0
    point2_elevation = 0

    api_url = f"https://api.open-elevation.com/api/v1/lookup?locations={point1[0]},{point1[1]}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        # Extract elevation from the response
        point1_elevation = data['results'][0]['elevation']
    else:
        point1_elevation = 0

    api_url = f"https://api.open-elevation.com/api/v1/lookup?locations={point2[0]},{point2[1]}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        # Extract elevation from the response
        point2_elevation = data['results'][0]['elevation']
    else:
        point2_elevation = 0

    total_elevation_gain += point2_elevation - point1_elevation
    return [total_distance,total_elevation_gain]

  
keyset = list(way_objects.keys())
print("Original keys: ",len(keyset) )
print("Broken keys: ",len(broken_way_objects.keys()) )

for newkey in broken_way_objects.keys():
    original_key = newkey.split("_")[0]
    if(original_key in keyset):
        keyset.remove(original_key)
    keyset.append(newkey)

#lets combine two objects now
broken_way_objects.update(way_objects)
#lets remove keys which we do not need now
print("All keys after merging: ",len(broken_way_objects.keys()) )

# ^ this will determine the final keyset
new_ways = {}
for key in list(way_metrics.keys()):
    new_ways[key] = broken_way_objects[key]

print("Num of keys in final object: ",len(new_ways.keys()) )


#graph creation starts
G = nx.DiGraph()


way_relations = {}
not_first_ways = [] #stores all the ways which are never first i.e children

# Create nodes for each way ID
for wayid in new_ways:
    way_relations[wayid] = []
    G.add_node(wayid)

# Create edges based on proximity
for wayid, coordinates in new_ways.items():
    end_point = tuple(coordinates[-1])
    for other_wayid, other_coordinates in new_ways.items():
        if wayid != other_wayid:
            start_point_other = tuple(other_coordinates[0])
            if is_within_distance(end_point, start_point_other):
                way_relations[wayid].append(other_wayid)
                not_first_ways.append(other_wayid)
                G.add_edge(wayid, other_wayid)

def get_trails(minimum_distance, maximum_distance, minimum_elevation_gain, maximum_elevation_gain):
    root_nodes = [node for node in G if G.in_degree(node) == 0]

    all_trails = []
    distance_in_meters = maximum_distance
    vert_in_meters = maximum_elevation_gain
    for root in range(len(root_nodes)):
        all_trails.extend(dfs_find_trails_in_range(G, root_nodes[root], minimum_distance, maximum_distance,  minimum_elevation_gain, maximum_elevation_gain, distance_tolerance=30, elevation_tolerance =30))

    print("Number of trails found: {}".format(len(all_trails)))
    # polylines = []
    coordinates = []
    # Add each trail to the map
    count = 0
    results = []
    for trail_set in all_trails:  # Assuming all_trails is a list of trails
        trail_coordinates = []
        for each_trail in trail_set:
            trail_coordinates.extend(new_ways[each_trail])  # Convert way IDs to coordinates


        #printout info about that trail
        # dist,ele = get_distance_elevation(trail_coordinates)
        dist = 0
        ele = 0
        # geojson_polyline = coordinates_to_geojson(coordinates)

        coordinates.append(trail_coordinates)
        # polylines.append(geojson_polyline)
        print("Trail Distance: {} Trail Elevation: {}".format(dist, ele))
        count += 1
        reserved_coords = [] #to get long, lat format
        for each in trail_coordinates:
            reserved_coords.append([each[1], each[0]])
        results.append(
            {
                "id" : count, 
                "distance": dist,
                "elevation": ele,
                "coordinates": reserved_coords
            }
        )
    
    final_result = {
        "data": results
    }

    with open("trail_search_results.json", "w+") as fp:
        json.dump(final_result, fp)


    return final_result


# print(len(get_trails(600, 1000, 100, 500)))
# print(count_nodes)
import json
import shapely
from shapely.geometry import Point
#to get the intersections, we use R-tree
from shapely.geometry import LineString
from shapely.ops import unary_union
import rtree


####THIS IS converting N intersections to 1, by taking the last intersection point
def find_closest_index(coords, point):
    """Find the index of the coordinate in coords that is closest to point."""
    point = Point(point)
    min_dist = float('inf')
    closest_index = None
    for i, coord in enumerate(coords):
        dist = Point(coord).distance(point)

        # if you see the results, the min dist is always 0, because obviously, they intersect
        if dist < min_dist:
            min_dist = dist
            closest_index = i

    return closest_index


#we work with all way onjects to get the intersections
with open('way_objects.json') as fp:
    way_objects = json.load(fp)



# Assuming way_objects is your data with {wayid: [(lat, long), ...]}
index = rtree.index.Index()
lines = {}

for wayid, coords in way_objects.items():
    line = LineString(coords)
    lines[int(wayid)] = line
    index.insert(int(wayid), line.bounds)

intersections = set()

new_broken_ways = {}
# Now, use this function in your loop
for wayid, line in lines.items():
    potential_intersects = list(index.intersection(line.bounds))

    break_points = []

    for other_wayid in potential_intersects:
        if wayid != other_wayid:
            other_line = lines[other_wayid]
            if line.intersects(other_line):
                intersection_point = line.intersection(other_line)
                intersections.add(intersection_point) #will use this as visualisation

                if isinstance(intersection_point, Point):
                    break_points.append(intersection_point)
                elif isinstance(intersection_point, shapely.geometry.MultiPoint):
                    for point in intersection_point.geoms:
                        break_points.append(point)



    # Sort break points along the line
    sorted_break_points = sorted(break_points, key=lambda p: find_closest_index(way_objects[str(wayid)], (p.x, p.y)))


    # Slice the way at each break point
    start_index = 0
    
    for i, breakpoint in enumerate(sorted_break_points):
        if isinstance(breakpoint, shapely.geometry.Point):
            closest_idx = find_closest_index(way_objects[str(wayid)], (breakpoint.x, breakpoint.y))
            new_broken_ways[str(wayid) + '_' + str(i)] = way_objects[str(wayid)][start_index:closest_idx + 1]
            start_index = closest_idx

    # Add the last segment if necessary
    if start_index < len(way_objects[str(wayid)]):
        new_broken_ways[str(wayid) + '_' + str(len(sorted_break_points))] = way_objects[str(wayid)][start_index:]

# Now, intersections set contains the intersection points
# print((new_broken_ways))
with open('broken_way_objects.json', 'w+') as fp:
    json.dump(new_broken_ways, fp)


import folium

# Create a map object
first_line = next(iter(lines.values()))
map_center = [first_line.coords[0][0], first_line.coords[0][1]]
m = folium.Map(location=map_center, zoom_start=15)
m = folium.Map(location=map_center, zoom_start=15)

# Add markers for the intersection points
for intersection in intersections:
    if not intersection.is_empty:
        if isinstance(intersection, shapely.geometry.MultiPoint):
            for point in intersection.geoms:
                pass
                # folium.Marker([point.x, point.y], popup="Intersection").add_to(m)
        elif isinstance(intersection, shapely.geometry.Point):
            folium.Marker([intersection.x, intersection.y], popup="Intersection {}".format([intersection.x, intersection.y])).add_to(m)

# Save the map or display it
m.save("intersections_map.html")



# Create a map object, centered on the bounding box average coordinates
avg_lat = sum(coord[0] for  wayid, coordinates in new_broken_ways.items() for coord in coordinates) / sum(len(coordinates) for wayid, coordinates in new_broken_ways.items())
avg_lon = sum(coord[1] for  wayid, coordinates in new_broken_ways.items() for coord in coordinates) / sum(len(coordinates) for wayid, coordinates in new_broken_ways.items())
map_osm = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)


way_objects = {}
for wayid, coordinates in new_broken_ways.items():
    # Extract the coordinates for the way
    # Create a polyline with the coordinates and add to the map
    # print(wayid)
    folium.PolyLine(coordinates, color="orange", weight=2.5, opacity=1).add_to(map_osm)
    # Optionally, add a marker for the first node of the way with a popup for the way ID
    folium.Marker(
        [coordinates[0][0], coordinates[0][1]],
        popup=f"Start Way ID: {wayid}",
        icon=folium.Icon(color='green')
    ).add_to(map_osm)

    try:
        folium.Marker(
            [coordinates[-2][0], coordinates[-2][1]],
            popup=f"End Way ID: {wayid}",
            icon=folium.Icon(color='red')
        ).add_to(map_osm)
    except:
        pass


# Save to an HTML file
output_file = './osm_broken_way_visualization.html'
map_osm.save(output_file)
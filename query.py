#Code which downloads the ways

import overpy
import folium
import json

# Initialize the Overpass API
api = overpy.Overpass()

# Define your bounding box values
bbox = (39.9245, -105.3364, 39.9978, -105.2691)

# Create a string representation of the bounding box
bbox_string = "{},{},{},{}".format(*bbox)

# Construct the Overpass query with the bounding box
query = """
    way["highway"="path"]({});
    (._;>;);
    out body;
""".format(bbox_string)

# Execute the Overpass API query
result = api.query(query)

# Create a map object, centered on the bounding box average coordinates
avg_lat = sum(node.lat for way in result.ways for node in way.nodes) / sum(len(way.nodes) for way in result.ways)
avg_lon = sum(node.lon for way in result.ways for node in way.nodes) / sum(len(way.nodes) for way in result.ways)
map_osm = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)

# Loop through each way and add them to the map
print("Number of ways found: ",len(result.ways))

way_objects = {}
for way in result.ways:
    # Extract the coordinates for the way
    coordinates = [(float(node.lat), float(node.lon)) for node in way.nodes]
    # Create a polyline with the coordinates and add to the map
    
    #storing it in the temporary database
    way_objects[way.id] = coordinates

    folium.PolyLine(coordinates, color="blue", weight=2.5, opacity=1).add_to(map_osm)
    # Optionally, add a marker for the first node of the way with a popup for the way ID
    folium.Marker(
        [way.nodes[0].lat, way.nodes[0].lon],
        popup=f"Way ID: {way.id}"
    ).add_to(map_osm)

with open('way_objects.json', 'w+') as fp:
    json.dump(way_objects, fp)

# Save to an HTML file
output_file = './osm_way_visualization.html'
map_osm.save(output_file)

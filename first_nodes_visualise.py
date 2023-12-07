#Code to visualise the first nodes
import json
import folium


with open('first_way_objects.json') as fp:
    first_way_objects = json.load(fp)



avg_lat = sum(coord[0] for  wayid, coordinates in first_way_objects.items() for coord in coordinates) / sum(len(coordinates) for wayid, coordinates in first_way_objects.items())
avg_lon = sum(coord[1] for  wayid, coordinates in first_way_objects.items() for coord in coordinates) / sum(len(coordinates) for wayid, coordinates in first_way_objects.items())
map_osm = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)


way_objects = {}
for wayid, coordinates in first_way_objects.items():
    # Extract the coordinates for the way
    # Create a polyline with the coordinates and add to the map
    
    #storing it in the temporary database
    # way_objects[wayid] = coordinates

    folium.PolyLine(coordinates, color="orange", weight=2.5, opacity=1).add_to(map_osm)
    # Optionally, add a marker for the first node of the way with a popup for the way ID
    folium.Marker(
        [coordinates[0][0], coordinates[0][1]],
        popup=f"Start Way ID: {wayid}"
    ).add_to(map_osm)


# Save to an HTML file
output_file = './osm_first_way_visualization.html'
map_osm.save(output_file)
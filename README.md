## Trail Finder

### File descriptions

1. `query.py` - Downloads the ways (trails) from OSM. Visualises them in `osm_way_visualization.html` and also stores the downloaded ways in `way_objects.json` so that you do not have to run the file again and download it.

2. `graph.py` - Forms a graph with a way as a node, and other ways as its child nodes if those ways start where the parent way ends. Also, finds all the ways with no parents, and stores them in `first_way_objects.json` - Not a super important file for the pipeline.

3. `first_nodes_visualise.py` - Just visualises the ways in the above file, and stores that visualisation in `osm_first_way_visualization.html` - It is useful to see the beginning of a lot of trails. 

4. `get_intersections.py` - SUPER IMPORTANT. - Go through all the ways, and finds intersections. Then breaks each way down into smaller trails. 

5. `get_way_gradients.ipynb` - SUPER IMPORTANT - `way_metrics.json` is calculated here which contains metrics of the smaller broken ways
### Upcoming tasks

1. Store new broken down ways, and build a new graph with all these ways. Remember to discard original ways, which were later broken down. 

2. Add properties to every edge of the graph, and node (trail properties - gradient, distance, elevation gain)
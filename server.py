from flask import Flask, request, send_file
import json
from flask_cors import CORS
import server_support_get_trails
import gpxpy
import gpxpy.gpx
import os

app = Flask(__name__)
CORS(app)

@app.route('/get-trails', methods=['POST'])
def get_trails():
    distance_minimum = int(request.json['distance_minimum'])
    distance_maximum = int(request.json['distance_maximum'])

    elevation_gain_minimum = int(request.json['elevation_gain_minimum'])
    elevation_gain_maximum = int(request.json['elevation_gain_maximum'])

    print(
        distance_minimum,
        distance_maximum,
        elevation_gain_minimum,
        elevation_gain_maximum
    )

    results = server_support_get_trails.get_trails(
        distance_minimum*1000, #converting to meters
        distance_maximum*1000,
        elevation_gain_minimum,
        elevation_gain_maximum
    )

    # with open("trail_search_results.json") as fp:
    #     trail_search_results = json.load(fp)

    return json.dumps(results['data'])

@app.route('/get-gpx', methods=['POST'])
def get_gpx():
    coordinates = request.json['coordinates']


    gpx = gpxpy.gpx.GPX()

    # # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # # Create points:
    for point in coordinates:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(point[1], point[0], elevation=0))

    # Generate GPX file content
    gpx_data = gpx.to_xml()

    # Write to a temporary file
    file_name = 'route_gpx_file.gpx'
    with open(file_name, 'w') as f:
        f.write(gpx_data)

    # Return the file as a response
    response = send_file(file_name, as_attachment=True)

    # Optionally, delete the file after sending it
    os.remove(file_name)

    return response

        
if __name__ == '__main__':
    app.run(debug=True)
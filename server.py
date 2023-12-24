from flask import Flask, request, send_file
import json
from flask_cors import CORS
import gpxpy
import gpxpy.gpx
import os
from geopy.distance import geodesic
from werkzeug.utils import secure_filename

import server_support_get_trails
import gpx_analysis

app = Flask(__name__)
CORS(app)

@app.route('/get-trails', methods=['POST'])
def get_trails():
    distance_minimum = int(request.json['distance_minimum'])
    distance_maximum = int(request.json['distance_maximum'])

    elevation_gain_minimum = int(request.json['elevation_gain_minimum'])
    elevation_gain_maximum = int(request.json['elevation_gain_maximum'])

    elevation_loss_minimum = int(request.json['elevation_loss_minimum'])
    elevation_loss_maximum = int(request.json['elevation_loss_maximum'])

    print(
        distance_minimum,
        distance_maximum,
        elevation_gain_minimum,
        elevation_gain_maximum,
        elevation_loss_minimum,
        elevation_loss_maximum
    )

    results = server_support_get_trails.get_trails(
        distance_minimum*1000, #converting to meters
        distance_maximum*1000,
        elevation_gain_minimum,
        elevation_gain_maximum,
        elevation_loss_minimum,
        elevation_loss_maximum
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


@app.route('/get-elevation-profile', methods=['POST'])
def get_elevation_profile():
    file = None
    race = None
    # Check if the post request has the file part
    if 'file' in request.files:
        file = request.files['file']

    else:
        race = request.json['race']

    if file:
        # Parse GPX file
        gpx = gpxpy.parse(file)

        # new_file_path = os.path.join('./uploads/', new_filename)
        with open('./user_files/{}'.format(file.filename), 'w') as new_gpx_file:
            new_gpx_file.write(gpx.to_xml())

        parsed_gpx = []
        total_distance = 0

        for track in gpx.tracks:
            for segment in track.segments:
                for i in range(1, len(segment.points)):
                    point1 = segment.points[i - 1]
                    point2 = segment.points[i]
                    distance = geodesic((point1.latitude, point1.longitude), (point2.latitude, point2.longitude)).meters
                    total_distance += distance
                    parsed_gpx.append({"distance": total_distance, "elevation": point2.elevation})

        # Return the parsed GPX data
        return {"data": parsed_gpx}
    
    if race:
        gpx_file = open('./official_files/{}.gpx'.format(race), 'r')
        gpx = gpxpy.parse(gpx_file)

        parsed_gpx = []
        total_distance = 0
        for track in gpx.tracks:
            for segment in track.segments:
                for i in range(1, len(segment.points)):
                    point1 = segment.points[i - 1]
                    point2 = segment.points[i]
                    distance = geodesic((point1.latitude, point1.longitude), (point2.latitude, point2.longitude)).meters
                    total_distance += distance
                    parsed_gpx.append({"distance": total_distance, "elevation": point2.elevation})

        # Return the parsed GPX data
        return {"data": parsed_gpx}

    return {"error": "File upload failed"}, 500


@app.route('/analyse-gpx', methods=['POST'])
def analyse_gpx():
    type_val = request.json['type']
    if(type_val == 'race'):
        filename = request.json['race']
        segments = gpx_analysis.analyse('./official_files/{}.gpx'.format(filename))

    if(type_val == 'file'):
        filename = request.json['filename']
        segments = gpx_analysis.analyse('./user_files/{}'.format(filename))

    results = []
    count = 0

    for each in segments:

        if(each['type'] == 'climb'):
            elevation_gain_minimum = each['elevation_change'] - 50
            elevation_gain_maximum = each['elevation_change'] + 50
            elevation_loss_minimum = -99999
            elevation_loss_maximum = 999999

        if(each['type'] == 'descent'):
            elevation_loss_minimum = each['elevation_change'] - 50
            elevation_loss_maximum = each['elevation_change'] + 50
            elevation_gain_minimum = -99999
            elevation_gain_maximum = 999999
        
        if(each['type'] == 'flat'):
            elevation_gain_minimum = -99999
            elevation_gain_maximum = 99999
            elevation_loss_minimum = -99999
            elevation_loss_maximum = 999999

        print("**************")
        print(each)
        trails =  server_support_get_trails.get_trails(
        each['distance']-100, #adding a little range buffer
        each['distance']+100,
        elevation_gain_minimum,
        elevation_gain_maximum,
        elevation_loss_minimum,
        elevation_loss_maximum
        )['data']

        each['trails'] = trails
        count +=1
        each['id'] = count
        results.append(each)
        print("**************")
    
    return json.dumps(results)


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, request
import json
from flask_cors import CORS
import server_support_get_trails

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


if __name__ == '__main__':
    app.run(debug=True)
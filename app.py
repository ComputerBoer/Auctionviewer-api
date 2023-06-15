from traceback import print_exc
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import requests
from cache import Cache
from utils.auctionutils import getTwkAuctions, getAuctionlocations
from utils.locationutils import getGeoLocationByCity
from models.location import JsonEncoder
import json

app = Flask(__name__)
CORS(app, resources={r"/auction/*": {"origins": ["http://localhost:4200","https://auctionviewer.ikbenhenk.nl", "https://victorious-bay-0d278c903.3.azurestaticapps.net"]}})
application = app # our hosting requires application in passenger_wsgi

@app.route("/")
def gethome():
    return "application is working!"


@app.route("/auction/<countrycode>")
def get(countrycode):
    try:
        if countrycode not in ['NL', 'BE', 'DE']:
            print(f'country not available: {countrycode} ')
            return jsonify('NOT AVAILABLE COUNTRY')


        res = getAuctionlocations(countrycode)
        #return json.dumps(res, sort_keys=True, default=str)
        return JsonEncoder().encode(res)

    except Exception as e:
        print('something went wrong ')
        print_exc(e)
        return 'internal server error', 500

if __name__ == "__main__":
    app.run()  # run our Flask app



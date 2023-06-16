from traceback import print_exc
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import requests
from cache import Cache
from utils.auctionutils import getTwkAuctions, getAuctionlocations
from utils.locationutils import getGeoLocationByCity
from models.location import JsonEncoder

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:4200","https://auctionviewer.ikbenhenk.nl", "https://victorious-bay-0d278c903.3.azurestaticapps.net"]}})
application = app # our hosting requires application in passenger_wsgi

@app.route("/")
def gethome():
    return "application is working!"

@app.route("/v2/auction/<countrycode>")
def getAllAuctions(countrycode):
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


@app.route("/auction/<countrycode>")
def getTwkAuctions(countrycode):
    try:
        if countrycode not in ['NL', 'BE', 'DE']:
            print(f'country not available: {countrycode} ')
            return jsonify('NOT AVAILABLE COUNTRY')

        res = Cache.get(countrycode)
        if(res):
            return res.obj

        response = requests.get("https://api.troostwijkauctions.com/sale/4/listgrouped?batchSize=99999&CountryIDs=" + countrycode)
        print(f'request statuscode: {response.status_code} ')

        if(response.status_code ==200):
            Cache.add(countrycode, response.json())

        return response.json();

    except Exception as e:
        print('something went wrong ')
        print_exc(e)
        return 'internal server error', 500

if __name__ == "__main__":
    app.run()  # run our Flask app



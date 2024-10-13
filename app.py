from utils.helperutils import log
from traceback import print_exc
from flask import Flask, jsonify
from flask_cors import CORS
from cache import Cache
from utils.auctionutils import  getAuctionlocations
from models.location import JsonEncoder

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:4200","https://auctionviewer.ikbenhenk.nl"]}})
application = app # our hosting requires application in passenger_wsgi

@app.route("/")
def gethome():
    return "application is working!"

@app.route("/v2/auction/<countrycode>")
def getAllAuctions(countrycode):
    try:
        if countrycode not in ['NL', 'BE', 'DE']:
            log('country not available: ' + countrycode)
            return jsonify('NOT AVAILABLE COUNTRY')

        log('incoming api request')
        res = getAuctionlocations(countrycode)
        #return json.dumps(res, sort_keys=True, default=str)
        return JsonEncoder().encode(res)

    except Exception as e:
        log('something went wrong ')
        print_exc(e)
        return 'internal server error', 500

if __name__ == "__main__":
    app.run()  # run our Flask app



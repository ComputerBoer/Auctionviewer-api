from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
import requests
from config import Cache

app = Flask(__name__)
CORS(app, resources={r"/auction/*": {"origins": ["http://localhost:4200","https://auctionviewer.ikbenhenk.nl", "https://victorious-bay-0d278c903.3.azurestaticapps.net"]}})
application = app # our hosting requires application in passenger_wsgi

@app.route("/")
def gethome():
    return "application is working!"


@app.route("/auction/<countrycode>")
def get(countrycode):

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

if __name__ == "__main__":
    app.run()  # run our Flask app



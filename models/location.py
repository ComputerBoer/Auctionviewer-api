from enum import Enum
import enum
from json import JSONEncoder
import json

class Countrycode(Enum):
    NL = "NL",
    DE = "DE",
    BE = "BE"

class Auctionbrand(str, Enum):
    NONE = "NONE",
    TWK = "TWK"
    OVM = "OVM"
    AP = "AP"


class GeonameLocation:
    def __init__(self, geonameid = 0, name = "", asciiname = "", alternatenames = [], latitude = 0, longitude = 0, countrycode:Countrycode = Countrycode.NL, modificationdate = "") :
        self.geonameid = geonameid
        self.name = name
        self.asciiname = asciiname
        self.alternatenames = alternatenames
        self.latitude = latitude
        self.longitude = longitude
        self.countrycode = countrycode
        self.modificationdate = modificationdate

class Maplocation:
    def __init__(self, lat = 0, long = 0, numberofauctions = 0, geonamelocation:GeonameLocation = None, auctions = []):
        self.lat = lat
        self.long = long
        self.numberofauctions = numberofauctions
        self.geonamelocation = geonamelocation
        self.auctions = auctions

class Auction: 
    def __init__(self, auctionbrand: Auctionbrand = Auctionbrand.NONE, city = "", countrycode:Countrycode = Countrycode.NL, name = "", starttime = None, closingtime = None, url = "", imageurl = "", numberoflots = 0, geonamelocation: GeonameLocation =  None, multiplelocations = False):
        self.city = city
        self.countrycode = countrycode
        self.name = name
        self.starttime = str(starttime)
        self.closingtime = str(closingtime)
        self.url = url
        self.imageurl = imageurl
        self.numberoflots = numberoflots
        self.geonamelocation = geonamelocation
        self.brand = auctionbrand
        self.multiplelocations = multiplelocations

class JsonEncoder(JSONEncoder):
    # def default(self, o):
    #     return o.__dict__
    #try 2
    def default(self, obj):
        # Only serialize public, instance-level attributes
        if hasattr(obj, '__dict__'):
            return {
                key: self.serialize(value)
                for key, value in obj.__dict__.items()
                if not key.startswith('_')  # skip private/protected
            }
        return super().default(obj)

    def serialize(self, value):
        if isinstance(value, list):
            return [self.serialize(item) for item in value]
        elif isinstance(value, dict):
            return {k: self.serialize(v) for k, v in value.items()}
        elif isinstance(value, enum.Enum):
            return value.name  # or value.value
        elif hasattr(value, '__dict__'):
            return self.default(value)  # dive into nested object
        else:
            try:
                json.dumps(value)
                return value
            except (TypeError, OverflowError):
                return str(value)
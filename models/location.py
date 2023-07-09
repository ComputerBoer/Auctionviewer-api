from enum import Enum
from json import JSONEncoder

class Countrycode(Enum):
    NL = "NL",
    DE = "DE",
    BE = "BE"

class Auctionbrand(str, Enum):
    NONE = "NONE",
    TWK = "TWK"
    OVM = "OVM"


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
    def __init__(self, auctionbrand: Auctionbrand = Auctionbrand.NONE, city = "", countrycode:Countrycode = Countrycode.NL, name = "", starttime = None, closingtime = None, url = "", imageurl = "", numberoflots = 0, geonamelocation: GeonameLocation =  None):
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

class JsonEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
from traceback import print_exc
from cache import Cache, FileCache
from models.location import Auction, Auctionbrand, Countrycode, Maplocation, JsonEncoder
from utils.APutils import getAPAuctions
from utils.OVMutils import getOVMAuctions
from utils.TWKutils import getTwkAuctions
from utils.AUCTutils import getAuctivoAuctions
from utils.locationutils import getGeoLocationByCity
from utils.helperutils import log
from datetime import datetime


def safe_call(fn, *args, default=None, **kwargs):
    try:
        res = fn(*args, **kwargs)
        return res if res is not None else (default if default is not None else [])
    except Exception:
        log(f"error running {getattr(fn, '__name__', str(fn))}")
        print_exc()
        return default if default is not None else []

def getAuctionlocations(countrycode: Countrycode, clearcache:bool = False):
    cachename = 'allauctions_' + countrycode

    log("should clear chache with cachename: " + str(clearcache) + ", " + cachename)

    if(clearcache):
        res = FileCache.get(cachename, 0)
    else:
       res = FileCache.get(cachename)

    if(res): 
      return res
    
    twkauctions = []
    ovmauctions = []
    apauctions = []
    auctivoauctions = []

    twkauctions = safe_call(getTwkAuctions, countrycode)
    ovmauctions = safe_call(getOVMAuctions)
    apauctions = safe_call(getAPAuctions)
    auctivoauctions = safe_call(getAuctivoAuctions, countrycode)

    auctions = [*twkauctions, *ovmauctions, *apauctions, *auctivoauctions]
    #filters all auctions for this geonameid
    auctions = list(filter(lambda a: a.numberoflots > 0 , auctions))
    
    for auction in auctions:
        auction.geonamelocation = getGeoLocationByCity(auction.city, countrycode)

#filters all auctions for this geonameid
    auctions = list(filter(lambda a: a.numberoflots > 0 , auctions))
    
    geonameids = map(get_geonameid, auctions)
    uniquegeonameids = (list(set(geonameids)))

    maplocations = []

    #loops through the uniques geonameids
    for geoid in uniquegeonameids:
        
        #filters all auctions for this geonameid
        geoauctions = list(filter(lambda a: get_geonameid(a) == geoid , auctions))
        if(geoauctions):
            geoauctions = list({object_.url: object_ for object_ in geoauctions}.values())
            #gets the location (if it has any) for the geolocation
            location = geoauctions[0].geonamelocation
            if(location):
                maplocation = Maplocation(location.latitude, location.longitude, len(geoauctions), location, geoauctions)
                maplocations.append(maplocation)

    for location in maplocations:
        del location.geonamelocation #removes object which is not used anymore
        for auction in location.auctions:
            del auction.geonamelocation #removes object to not have duplicate data send to the server

    FileCache.add(cachename, maplocations)
    return maplocations

def get_geonameid(auction):
    if(auction.geonamelocation):
        return auction.geonamelocation.geonameid
    return None


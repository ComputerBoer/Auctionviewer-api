import requests
from traceback import print_exc
from cache import Cache, FileCache
from models.location import Auction, Auctionbrand, Countrycode, Maplocation, JsonEncoder
from utils.APutils import getAPAuctions
from utils.OVMutils import getOVMAuctions
from utils.TWKutils import getTwkAuctions
from utils.locationutils import getGeoLocationByCity
from utils.helperutils import log
from datetime import datetime

def getAuctionlocations(countrycode: Countrycode, clearcache:bool = False):
    cachename = 'allauctions_' + countrycode

    log("should clear chache with cachename: " + str(clearcache) + ", " + cachename)

    if(clearcache):
        res = FileCache.get(cachename, 1)
    else:
       res = FileCache.get(cachename)

    if(res): 
      return res
    
    twkauctions = []
    ovmauctions = []
    apauctions = []

    try:
        twkauctions = getTwkAuctions(countrycode)
    except Exception as e: 
        log('something went wrong while running the twk auctions request')
        print_exc(e)
    
    try:
         ovmauctions = getOVMAuctions() 
    except Exception as e: 
        log('something went wrong while running the OVM auctions request')
        print_exc(e)

    try:
         apauctions = getAPAuctions() 
    except Exception as e: 
        log('something went wrong while running the OVM auctions request')
        print_exc(e)


    auctions = [*twkauctions, *ovmauctions, *apauctions]
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


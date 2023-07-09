from asyncio.windows_events import NULL
import requests
from cache import Cache
from models.location import Auction, Auctionbrand, Countrycode, Maplocation
from utils.locationutils import getGeoLocationByCity
from datetime import datetime

def getAuctionlocations(countrycode: Countrycode):
    cachename = 'allauctions_' + countrycode

    res = Cache.get(cachename)
    if(res): return res
    

    twkauctions = getTwkAuctions(countrycode)
    ovmauctions = getOVMAuctions() 
    auctions = [*twkauctions, *ovmauctions]

    for auction in auctions:
        auction.geonamelocation = getGeoLocationByCity(auction.city, countrycode)
        
    geonameids = map(get_geonameid, auctions)
    uniquegeonameids = (list(set(geonameids)))

    maplocations = []

    #loops through the uniques geonameids
    for geoid in uniquegeonameids:
        #filters all auctions for this geonameid
        geoauctions = list(filter(lambda a: get_geonameid(a) == geoid , auctions))
        if(geoauctions):
            #gets the location (if it has any) for the geolocation
            location = geoauctions[0].geonamelocation
            if(location):
                maplocation = Maplocation(location.latitude, location.longitude, len(geoauctions), location, geoauctions)
                maplocations.append(maplocation);

    for location in maplocations:
        del location.geonamelocation #removes object which is not used anymore
        for auction in location.auctions:
            del auction.geonamelocation #removes object to not have duplicate data send to the server

    Cache.add(cachename, maplocations)
    return maplocations

def get_geonameid(auction):
    if(auction.geonamelocation):
        return auction.geonamelocation.geonameid
    return None


def getTwkAuctions(countrycode):
    cachename = 'TwkAuctions_'+ countrycode
    res = Cache.get(cachename)
    if(res):return res

    response = requests.get("https://api.troostwijkauctions.com/sale/4/listgrouped?batchSize=99999&CountryIDs=" + countrycode)

    if(response.status_code ==200):
        print('Got Twk Auctions')
        data = response.json();
        auctions = []
        for result in data['results']:
            for twka in result['items']:
                a = Auction(Auctionbrand.TWK, twka['c'], twka['cc'], twka['n'], datetime.fromtimestamp(twka['sd']), datetime.fromtimestamp(twka['cd']), twka['url'], twka['ii'], twka['nol'] )
                auctions.append(a)
        Cache.add(cachename, auctions)

        return auctions
    return None

def getOVMAuctions():
    cachename = 'OnlineVeiling_'
    res = Cache.get(cachename)
    if(res):return res

    response = requests.get("https://onlineveilingmeester.nl/rest/nl/veilingen?status=open&domein=ONLINEVEILINGMEESTER")

    if(response.status_code ==200):
        data = response.json()
        auctions = []
        for result in data['veilingen']:
              cityname ="Nederland"  if result['isBezorgVeiling'] else result['afgifteAdres']['plaats'] 
              cityname = "Nederland" if cityname is None else cityname #there can be auctions where you have to make an appointment to retrieve the lots
              a = Auction(Auctionbrand.OVM, cityname,result['land'], result['naam'],result['openingsDatumISO'], result['sluitingsDatumISO'], str(result['land']).lower() + '/veilingen/' + str(result['id']) + '/kavels', 'images/150x150/' + str(result['id']) + '/' + result['image'], result['totaalKavels'] )
              auctions.append(a)
        Cache.add(cachename, auctions)
        return auctions
    return None
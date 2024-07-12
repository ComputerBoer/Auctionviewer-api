import imp
import requests
from traceback import print_exc
from cache import Cache, FileCache
from models.location import Auction, Auctionbrand, Countrycode, Maplocation, JsonEncoder
from utils.locationutils import getGeoLocationByCity
from utils.helperutils import log
from datetime import datetime
import re
import math

def getAuctionlocations(countrycode: Countrycode):
    cachename = 'allauctions_' + countrycode

    res = FileCache.get(cachename, 23)

    # res = Cache.get(cachename)
    if(res): 
      return res
    
    twkauctions = []
    ovmauctions = []

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

    FileCache.add(cachename, maplocations)
    return maplocations

def get_geonameid(auction):
    if(auction.geonamelocation):
        return auction.geonamelocation.geonameid
    return None

# global twkDataUrl; # = ''; #  'https://www.troostwijkauctions.com/_next/data/' #e6-N0pLHv12LVGS0oYzx6/nl/'


def getTWKUrl():
    response = requests.get('https://www.troostwijkauctions.com/')
    if(response.status_code ==200):
      buildid = re.search(r'"buildId":"([^"]*)', response.text, re.MULTILINE )
      twkDataUrl = 'https://www.troostwijkauctions.com/_next/data/' + str(buildid[1]) + '/nl/'
      log('buildid: ' + str(buildid[1]))
      log('twkDataUrl: ' + twkDataUrl)
      return twkDataUrl

    return None


def getTwkAuctions(countrycode):
    cachename = 'TwkAuctions_'+ countrycode
    res = Cache.get(cachename)
    if(res):
      return res

    # buildidresponse = requests.get('https://www.troostwijkauctions.com/')
    twkDataUrl = getTWKUrl();

    if(twkDataUrl is None):
        return [];

    response = requests.get(twkDataUrl + "auctions.json?countries=" + countrycode)

    if(response.status_code ==200):
        log('Got Twk Auctions')
        data = response.json();
        auctions = [];
        
        totalAuctionCount = data['pageProps']['auctionList']['totalSize'];
        pages = math.ceil(totalAuctionCount / len(data['pageProps']['auctionList']['results']))
        # for result in data['pageProps']['auctionList']:
        
        for i in range(1,pages,1):
          log("getting page " + str(i) + ' of ' + str(pages))
          if(i > 1):
              response = requests.get(twkDataUrl + "auctions.json?countries=" + countrycode + "&page=" + str(i));
              data = response.json();
          
          for twka in data['pageProps']['auctionList']['results']:
            # print(twka['urlSlug'])
            auction = getTWKAuction(twkDataUrl, twka['urlSlug'])
            if(auction):
              auctions.append(auction)
        Cache.add(cachename, auctions)

        return auctions
    return []

def getTWKAuction(twkDataUrl, auctionurlslug):
    response = requests.get(twkDataUrl + "a/" + auctionurlslug + '.json')
    if(response.status_code == 200):
        data = response.json();
        if(len(data['pageProps']['lots']['results']) ==0):
          return None;
    
        twka = data['pageProps']['auction'];
        firstlot = data['pageProps']['lots']['results'][0]
        city = "Nederland" if  firstlot['location']['city'].lower() == 'online' or firstlot['location']['city'].lower() == "free delivery" else firstlot['location']['city']
        # if(firstlot['location']['city'].lower() != 'online'):
        #   city = firstlot['location']['city'];
        a = Auction(Auctionbrand.TWK, city, firstlot['location']['countryCode'].upper(), twka['name'], datetime.fromtimestamp(twka['startDate']), datetime.fromtimestamp(twka['minEndDate']), '/a/' + auctionurlslug, twka['image']['url'], twka['lotCount'] )
        # print(a);
        return a;

    return None

def getOVMAuctions():
    cachename = 'OnlineVeiling_'
    res = Cache.get(cachename)
    if(res):
      return res

    try:
      response = requests.get("https://onlineveilingmeester.nl/rest/nl/veilingen?status=open&domein=ONLINEVEILINGMEESTER")
    except:
        log("The OVM auctions call threw a error")

    if(response is None):
       return []
      
    if(response.status_code ==200):
        log('Got Ovm Auctions')
        try:
           data = response.json()
           auctions = []
           for result in data['veilingen']:
               cityname ="Nederland"  if result['isBezorgVeiling'] else result['afgifteAdres']['plaats'] 
               cityname = "Nederland" if cityname is None else cityname #there can be auctions where you have to make an appointment to retrieve the lots
               startdatetime = result['openingsDatumISO'].replace("T", " ").replace("Z", "")
               enddatetime = result['sluitingsDatumISO'].replace("T", " ").replace("Z", "")
               image = "";
               #if hasattr(result, 'image') : #result['image'] :
               image = result.get('image', "")  #['image']
               if image == "":
                  image = result.get('imageList', [""])[0]
               
               a = Auction(Auctionbrand.OVM, cityname,result['land'], result['naam'],startdatetime, enddatetime, str(result['land']).lower() + '/veilingen/' + str(result['id']) + '/kavels', 'images/150x150/' + image, result['totaalKavels'] )
               auctions.append(a)
           Cache.add(cachename, auctions)
           return auctions
        except Exception as e:
           log('Something went wrong in the mapping of OVM auctions to auctionviewer objects. The reason was: ' + response.reason  + '. The response was: ' + JsonEncoder().encode(response.json()))
           print_exc(e)
        
    else:
       log("The OVM auctions call didn't gave a 200 response but a " + str(response.status_code) + ". With the reason: " + response.reason)
    return []
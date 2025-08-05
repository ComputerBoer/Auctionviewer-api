from datetime import datetime
import math
import re
import requests

from cache import Cache
from models.location import Auction, Auctionbrand
from utils.helperutils import log


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
    twkDataUrl = getTWKUrl()

    if(twkDataUrl is None):
        return []

    response = requests.get(twkDataUrl + "auctions.json?countries=" + countrycode)

    if(response.status_code ==200):
        log('Got Twk Auctions')
        data = response.json()
        auctions = []
        
        totalAuctionCount = data['pageProps']['totalSize'];
        pages = math.ceil(totalAuctionCount / data['pageProps']['pageSize'])
        # for result in data['pageProps']['auctionList']:
        
        for i in range(1,pages,1):
          log("getting page " + str(i) + ' of ' + str(pages))
          if(i > 1):
              response = requests.get(twkDataUrl + "auctions.json?countries=" + countrycode + "&page=" + str(i))
              data = response.json()
          
          for twka in data['pageProps']['listData']:
            # print(twka['urlSlug'])
            auctionlocations = getTWKAuction(twka)
            for auction in auctionlocations:
              auctions.append(auction)

        Cache.add(cachename, auctions)

        return auctions
    return []

def getTWKAuction(twka):
    locations = []
    cities = []

    if(len(twka['collectionDays'])>0):
      cities = twka['collectionDays']
    elif(len(twka['deliveryCountries']) >0):
      cities = [{ 'countryCode': 'nl', 'city':'Nederland'}]

    image = ''
    if(len(twka['images']) > 0 and twka['images'][0]['url']):
       image = twka['images'][0]['url']

    for city in cities:
      if(city['countryCode'].upper() != 'NL'): continue
      a = Auction(Auctionbrand.TWK, city['city'], city['countryCode'].upper(), twka['name'], datetime.fromtimestamp(twka['startDate']), datetime.fromtimestamp(twka['minEndDate']), '/a/' + twka['urlSlug'], image, twka['lotCount'], None, len(cities) > 1 )
      locations.append(a)
    
    return locations
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
            auction = getTWKAuction(twkDataUrl, twka['urlSlug'])
            if(auction):
              auctions.append(auction)
        Cache.add(cachename, auctions)

        return auctions
    return []

def getTWKAuction(twkDataUrl, auctionurlslug):
    log("getting TWK auctiondetails:" + twkDataUrl + "a/" + auctionurlslug + ".json")
    response = requests.get(twkDataUrl + "a/" + auctionurlslug + '.json')
    if(response.status_code == 200):
        data = response.json()
        if(len(data['pageProps']['lots']['results']) ==0):
          return None
    
        twka = data['pageProps']['auction']
        firstlot = data['pageProps']['lots']['results'][0]
        city = "Nederland" if  firstlot['location']['city'].lower() == 'online' or firstlot['location']['city'].lower() == "free delivery" else firstlot['location']['city']
        a = Auction(Auctionbrand.TWK, city, firstlot['location']['countryCode'].upper(), twka['name'], datetime.fromtimestamp(twka['startDate']), datetime.fromtimestamp(twka['minEndDate']), '/a/' + auctionurlslug, twka['image']['url'], twka['lotCount'] )
        # print(a);
        return a

    return None
from datetime import datetime
import math
import re
import requests

from cache import Cache
from models.location import Auction, Auctionbrand, Countrycode, JsonEncoder
from utils.helperutils import log


TROOSTWIJK_GRAPHQL_URL = "https://storefront.tbauctions.com/storefront/graphql"

ALLAUCTIONS_QUERY = """query AllAuctions(
    $request:AllAuctionsInput!
    $platform:Platform!
    ){
        allAuctions:allAuctionsV2(
            request:$request 
            platform:$platform
        ){
            results{
            ...listingAuction
            }
            totalSize 
            pageNumber
        }
    }fragment listingAuction on Auction{
        id 
        displayId 
        name 
        urlSlug 
        directSaleType 
        biddingStatus 
        endDate 
        startDate 
        images{
            url 
            alt 
            order
        }
        lotCount 
        collectionDays{
            countryCode 
            city
        }
        deliveryCountries 
        url3dTour 
        minEndDate 
        image{
            url 
            alt
        }
    }"""

def getTWKGraphQLPayload(pagenum = 1):
    # 

    return {
        # "operationName": "QueryPublicationPreviewsFrontPage",
        "variables": {
          "request":{
            "locale":"nl",
            "biddingStatuses":["BIDDING_OPEN","BIDDING_NOT_YET_OPENED"],
            "sortBy":"END_DATE_ASC",
            "pageNumber":pagenum,
            "pageSize":50,
            "facets":[{
              "identifier":"countries",
              "values":["nl"]
            }],
            "rangeFacets":[]
          },
          "platform":"TWK"
        },
        "query": ALLAUCTIONS_QUERY
    }



def getTwkAuctions(countrycode: Countrycode = Countrycode.NL):
    cachename = 'TwkAuctions_'+ countrycode
    res = Cache.get(cachename)
    if(res):
      return res

    response = requests.post( TROOSTWIJK_GRAPHQL_URL, json=getTWKGraphQLPayload(1) ) # headers=HEADERS,
    if response.status_code != 200:
        log(f"TWK GraphQL request failed: {response.status_code}")
        return []

    log('Got Twk Auctions')
    auctions = []
    
    totalAuctionCount = response.json().get('data', {}).get('allAuctions', {}).get('totalSize')
    pages = math.ceil(totalAuctionCount / 50)

    auctions = iterateAuctions(response.json().get('data', {}).get('allAuctions', {}).get('results', []))
    
    for pagenum in range(2,pages,1):
      log("getting page " + str(pagenum) + ' of ' + str(pages))

      response = requests.post( TROOSTWIJK_GRAPHQL_URL, json=getTWKGraphQLPayload(pagenum) ) # headers=HEADERS,
      if response.status_code != 200:
        log(f"TWK GraphQL request failed: {response.status_code}")
        continue

      auctions = auctions + iterateAuctions(response.json().get('data', {}).get('allAuctions', {}).get('results', []))

    Cache.add(cachename, auctions)

    return auctions

def iterateAuctions(auctionresults):
  auctions = []
  for twka in auctionresults:
    auctions = auctions +getTWKAuction(twka)
  return auctions
      

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
      if(city['countryCode'] is None ): continue
      if(city['countryCode'].upper() != 'NL'): continue
      
      a = Auction(
         Auctionbrand.TWK, 
         city['city'], 
         city['countryCode'].upper(), 
         twka['name'], 
         datetime.fromtimestamp(twka['startDate']), 
         datetime.fromtimestamp(twka['minEndDate']), 
         '/a/' + twka['urlSlug'], 
         image, 
         twka.get('lotCount', 0), 
         None, 
         len(cities) > 1 
         )
      locations.append(a)
    
    return locations
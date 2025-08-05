

from datetime import datetime
import json
import re
from time import ctime
from traceback import print_exc
import requests
from cache import Cache
from models.location import Auction, Auctionbrand, Countrycode, JsonEncoder
from utils.helperutils import log


def getAPAuctions():
    cachename = 'AuctionPort_'
    res = Cache.get(cachename)
    if(res):
      return res

    try:
      response = requests.get("https://api.auctionport.be/auctions/small?size=100&page=1")
    except:
        log("The Auctionport auctions call threw a error")

    if(response is None):
       return []
      
    if(response.status_code ==200):
        log('Got AP Auctions')
        try:
            data = response.json()
            pages = data['pages']
            auctions = []
            for i in range(0,pages-1,1):
                log("getting page " + str(i) + ' of ' + str(pages))
                # if(i > 1):
                response = requests.get("https://api.auctionport.be/auctions/small?size=100&page=" + str(i))
                if(response is None): continue
                if(response.status_code != 200): continue

                data = response.json()
                
                for PAauction in data['data']:
                    #makes sure that the locations array is filled with at least one location
                    if PAauction['locations'] == []: 
                        PAauction['locations'] = [PAauction['location']]

                    #makes sure that the auction is still active
                    closingdate = datetime.fromisoformat(PAauction['closingDate'])
                    if(closingdate.date() < datetime.now().date() ): continue
                    if(PAauction['lotCount'] <= 0): continue

                    multipleLocations = len(PAauction['locations']) > 1

                    for location in PAauction['locations']:
                        if not location.endswith('Nederland'): continue
                        loc = re.sub('Nederland', '', location)
                        # loc = location.split(",")
                        postalcodeRegex = r'(.*?)[1-9][0-9]{3} ?(?!sa|sd|ss)[a-zA-Z]{2}'
                        city = re.sub(postalcodeRegex  , '', loc) #removes postalcode and everything in front of it
                        city = city.strip() #removes whitespace
                        city = city.strip(',') #removes trailing and leading ,
                        city = city.split(',') #splits on , to overcome not matching regex
                        city = city[len(city)-1]
                        city = city.strip()
                        newauction = Auction(Auctionbrand.AP,city, Countrycode.NL, PAauction['title'], datetime.fromisoformat(PAauction['openDate']), datetime.fromisoformat(PAauction['closingDate']), '/auction/'+ str(PAauction['id']), PAauction['imageUrl'], PAauction['lotCount'] , None, multipleLocations)

                        auctions.append(newauction)
            Cache.add(cachename, auctions)
            return auctions
        except Exception as e:
           log(e.__cause__ + '--  Something went wrong in the mapping of AP auctions to auctionviewer objects. The reason was: ' + response.reason  + '. The response was: ' + JsonEncoder().encode(response.json()))
           print_exc(e)
        
    else:
       log("The AP auctions call didn't gave a 200 response but a " + str(response.status_code) + ". With the reason: " + response.reason)
    return []
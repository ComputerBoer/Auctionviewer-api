from traceback import print_exc
import requests
from cache import Cache
from models.location import Auction, Auctionbrand, JsonEncoder
from utils.helperutils import log


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
               image = ""
               #if hasattr(result, 'image') : #result['image'] :
               image = result.get('image', "")  #['image']
               if image == "":
                  images = result.get('imageList')
                  if(len(images) >0):
                     image = images[0]
                  else:
                     log("No image found for OVM auction: " + result['naam'])
               
               a = Auction(Auctionbrand.OVM, cityname,result['land'], result['naam'],startdatetime, enddatetime, str(result['land']).lower() + '/veilingen/' + str(result['id']) + '/kavels', 'images/150x150/' + image, result['totaalKavels'] )
               auctions.append(a)
           Cache.add(cachename, auctions)
           return auctions
        except Exception as e:
           log(e.__cause__ + '--  Something went wrong in the mapping of OVM auctions to auctionviewer objects. The reason was: ' + response.reason  + '. The response was: ' + JsonEncoder().encode(response.json()))
           print_exc(e)
        
    else:
       log("The OVM auctions call didn't gave a 200 response but a " + str(response.status_code) + ". With the reason: " + response.reason)
    return []
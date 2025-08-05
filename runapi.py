import requests
# from utils.auctionutils import getAuctionlocations

# try:
#   getAuctionlocations('NL', True)
#   print('ran getauctions request successfull')  
# except Exception as e: 
#    print('A error occurred while running the getauctions request')
#    print(e)


response = requests.get('https://api.auctionviewer.ikbenhenk.nl//v2/refreshauction/NL')
if(response.status_code ==200):
  print('ran getauctions request successfull')  
else:
  print('A error occurred while running the getauctions request')  
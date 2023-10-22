import requests

response = requests.get('https://api.auctionviewer.ikbenhenk.nl//v2/auction/NL')
if(response.status_code ==200):
  print('ran getauctions request successfull')  
else:
  print('A error occurred while running the getauctions request')  
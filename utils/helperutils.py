from datetime import datetime, timedelta

def log(value):
   
    try: 
       print(str(datetime.now()) + ' ' + value.encode("utf-8"))
    except UnicodeEncodeError:
      print(str(datetime.now()) + ' print error')
   
    #print(u' '.join(( str(datetime.now()), value)).encode('utf-8').strip())
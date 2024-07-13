from datetime import datetime, timedelta

def log(value):
    print(str(datetime.now()) + ' ' + value)
    # try: 
    #    print(str(datetime.now()) + ' ' + value.encode("utf-8"))
    # except:
    #   print(str(datetime.now()) + ' print error')
   
    #print(u' '.join(( str(datetime.now()), value)).encode('utf-8').strip())
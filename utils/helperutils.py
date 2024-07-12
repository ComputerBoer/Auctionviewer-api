from datetime import datetime, timedelta

def log(value):
    print(u' '.join(( str(datetime.now()), value)).encode('utf-8').strip())
    # print( str(value))
from datetime import datetime, timedelta

def log(value):
    value = value.encode('ascii', errors='ignore')
    value = value.decode()
    print(str(datetime.now()) + ' ' + value)

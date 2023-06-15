from datetime import datetime, timedelta

cache = {}

class Cache():
    def get(key, notOlderThanHours = 24):
       #print('get key ' + key)
       if key in cache:
           cacheobj = cache[key] 
           if(not cache):
               return None
           if(cacheobj.isOlderThanHours(notOlderThanHours)):
               print('removing cacheobject ' + key)
               del cache[key]
               return None
           #print('returning cacheobject ' + key)
           return cacheobj.obj

    def add(key, obj):
        print('adding cacheobject ' + key)
        cacheobj = CacheObj(key, obj)
        cache[key] = cacheobj


class CacheObj:
    def __init__(self, key, obj):
        self.key = key
        self.obj = obj
        self.time=datetime.now()
    
    def isOlderThanHours(self, hours):
        #print(f'checking time cacheobject {self.time} < {datetime.now() - timedelta(hours=hours)}')
        return self.time < datetime.now() - timedelta(hours=hours)
    
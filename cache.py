from datetime import datetime, timedelta
import os.path
from pathlib import Path
import time
import json

from models.location import JsonEncoder

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
           print(str(datetime.now()) + ' returning cacheobject ' + key)
           return cacheobj.obj

    def add(key, obj):
        print(str(datetime.now()) + ' adding cacheobject ' + key)
        cacheobj = CacheObj(key, obj)
        cache[key] = cacheobj


class CacheObj:
    def __init__(self, key, obj):
        self.key = key
        self.obj = obj
        self.time=datetime.now()
    
    def isOlderThanHours(self, hours):
        print('checking time cacheobject ' + self.key + ': ' + str(self.time) + " < " + str(datetime.now() - timedelta(hours=hours)))
        return self.time < datetime.now() - timedelta(hours=hours)
  
      
class FileCache():
  def get(key, notOlderThanHours = 24):
      
      filepath = "./filecache/" + key + ".json"
      cachefile = Path(filepath)
      if cachefile.is_file():
        ti_m = os.path.getmtime(filepath)
        #checks last modified age of file, and removes it if it is too old
        print('checking time cachefile ' + filepath + ': ' + str(ti_m) + " < " + str(time.time() - (3600 * notOlderThanHours)))
        if(ti_m < time.time() - (3600 * notOlderThanHours)):
          print()
          os.remove(filepath);
          return None;
        
        with open(filepath) as json_file:
          json_data = json.load(json_file);
          print('returning json data from cachefile: ' + key)
          return json_data;
        
      return None

  def add(key, obj):
        print(str(datetime.now()) + ' adding filecacheobject ' + key);
        json_data = JsonEncoder().encode(obj)
        with open("./filecache/" + key + ".json", 'w') as f:
          f.write(json_data)
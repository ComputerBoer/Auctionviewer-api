import re
import os
from pathlib import Path
from cache import Cache, FileCache
from models.location import Countrycode, GeonameLocation, JsonEncoder
from utils.helperutils import log;

def getLocationArray(countrycode: Countrycode):
    cachename = 'locations_' + countrycode

    res = Cache.get(cachename,672) #a month in the cache is long enough...
    if(res):return res

    base_dir = Path(os.path.dirname(__file__)).parent.absolute() #<-- absolute dir the script is in
    #filename = "\data\locationfiles\\" + countrycode + ".txt"
    abs_file_path = os.path.join(base_dir, "data", "locationfiles", countrycode + ".txt")
    with open(abs_file_path, encoding='utf-8', errors='ignore') as f:
        #datalines = f.readlines();

        geonames = []
        for line in f:
            line = line.rstrip('\n');
            data = line.split("\t")
            alternatenames = []
            if data[3] != "":
                alternatenames = [d.strip() for d in data[3].lower().split(",")] #makes from comma seperated a lowercase array and strips leading and trailing white spaces 
            geoname = GeonameLocation(data[0], data[1].strip().lower(), data[2].strip().lower(), alternatenames, data[4], data[5], data[8], data[18])
            geonames.append(geoname)

        Cache.add(cachename,geonames)

        return geonames

def getGeoLocationByCity(city = "", countrycode: Countrycode = Countrycode.NL ):
    city = city.strip().lower(); #strips leading and trailing white spaces and makes it lowercase

    cityname = city
    if(not "gemeente" in cityname):
        cityname = "gemeente " + cityname

    geonames = getLocationArray(countrycode)

    # log('cityname and city: ' + cityname + " , " + city)

    #first tries name with 'gemeente as prefix'
    geo = list(filter(lambda g: g.name == cityname, geonames))
    if(geo): geo = geo[0]
    # print('first try' + repr(geo))
    if (geo): return geo;
    #also tries in the alternatenames
    geo = list(filter(lambda g: inAlternatenames(g.alternatenames, cityname), geonames))
    if(geo): geo = geo[0]
    #print('alternatenames'+ repr( geo))
    if (geo): return geo;
    
    #then tries name without 'gemeente as prefix'
    geo = list(filter(lambda g: g.name == city, geonames))
    if(geo): geo = geo[0]
    #print('without gemeente' + repr( geo))
    if (geo): return geo;
    #also tries in the alternatenames
    geo = list(filter(lambda g: inAlternatenames(g.alternatenames, city), geonames))
    if(geo): geo = geo[0]
    #print('alternatenames without gemeente' + repr( geo))
    if (geo): return geo;

    #removes everything between () and then removes the leading and trailing spaces;
    
    log('name before regex ' + city)
    #city = re.sub('/\([^()]*\)/g', '', city)
    city = re.sub("[\(].*?[\)]", "", city)
    city = city.strip();
    log('name after regex ' + city)

    geo = list(filter(lambda g: g.name == city, geonames))
    if(geo): geo = geo[0]
    #print('without anything between ()' + repr( geo))
    if (geo): return geo;
    

    #also tries in the alternatenames
    geo = list(filter(lambda g: inAlternatenames(g.alternatenames, city), geonames))
    if(geo): geo = geo[0]
    #print('alternatenames without ()'+ repr( geo))
    if (geo): return geo;

    log('city not found ' + city)
    return None;

def inAlternatenames(alternatenames = [], name = ""):
    return name in alternatenames
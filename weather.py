"""
Handles fetching and decoding weather.
"""

import re
import urllib
import csv
import json
import requests
from datetime import datetime, timedelta

INVALID = 'INVALID'
VFR = 'VFR'
MVFR = 'M' + VFR
IFR = 'IFR'
LIFR = 'L' + IFR
NIGHT = 'NIGHT'

RED = 'RED'
GREEN = 'GREEN'
BLUE = 'BLUE'
GRAY = 'GRAY'
YELLOW = 'YELLOW'
WHITE = 'WHITE'
LOW = 'LOW'
OFF = 'OFF'


__rest_session__ = requests.Session()
__daylight_cache__ = {}
__metar_report_cache__ = {}


def __load_airport_data__(airport_data_file="./data/airports.csv"):
    """
    Loads all of the airport and weather station data from the included CSV file
    then places it into a dictionary for easy use.

    Keyword Arguments:
        airport_data_file {str} -- The file that contains the airports (default: {"./data/airports.csv"})

    Returns:
        dictionary -- A map of the airport data keyed by IACO code.
    """

    csvfile = open(airport_data_file, 'r')

    fieldnames = ("id", "ident", "type", "name", "latitude_deg", "longitude_deg", "elevation_ft", "continent", "iso_country", "iso_region",
                  "municipality", "scheduled_service", "gps_code", "iata_code", "local_code", "home_link", "wikipedia_link", "keywords")
    reader = csv.DictReader(csvfile, fieldnames)

    airport_to_location = {}

    for row in reader:
        airport_to_location[row["ident"]] = {
            "lat": row["latitude_deg"], "long": row["longitude_deg"]}

    return airport_to_location


__airport_locations__ = __load_airport_data__()


def __get_utc_datetime__(datetime_string):
    """
    Parses the RFC format datetime into something we can use.

    Arguments:
        datetime_string {string} -- The RFC encoded datetime string.

    Returns:
        datetime -- The parsed date time.
    """

    return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S+00:00")

def __set_cache__(airport_iaco_code, cache, value):
    """
    Sets the given cache to have the given value.
    Automatically sets the cache saved time.
    
    Arguments:
        airport_iaco_code {str} -- The code of the station to cache the results for.
        cache {dictionary} -- The cache keyed by airport code.
        value {object} -- The value to store in the cache.
    """

    cache[airport_iaco_code] = (datetime.utcnow(), value)

def __is_cache_valid__(airport_iaco_code, cache, cache_life_in_minutes=15):
    """
    Returns TRUE and the cached value if the cached value
    can still be used.

    Arguments:
        airport_iaco_code {str} -- The airport code to get from the cache.
        cache {dictionary} -- Tuple of last update time and value keyed by airport code.
        cache_life_in_minutes {int} -- How many minutes until the cached value expires

    Returns:
        [type] -- [description]
    """

    if cache is None:
        return (False, None)

    now = datetime.utcnow()

    if airport_iaco_code in cache:
        time_since_last_fetch = now - cache[airport_iaco_code][0]

        if ((time_since_last_fetch.total_seconds()) / 60.0) < cache_life_in_minutes:
            return (True, cache[airport_iaco_code][1])
        else:
            return (False, cache[airport_iaco_code][1])

    return (False, None)


def get_civil_twilight(airport_iaco_code):
    """
    Gets the civil twilight time for the given airport

    Arguments:
        airport_iaco_code {string} -- The IACO code of the airport.

    Returns:
        When civil sunrise and sunset are in UTC
    """

    utc_time = datetime.utcnow()

    # Make sure that we are getting the sunrise/sunset for the current date
    # not the next day...
    if utc_time.hour < 12:
        utc_time = utc_time - timedelta(days=1)

    is_cache_valid, cached_value = __is_cache_valid__(
        airport_iaco_code, __daylight_cache__, 60)

    if is_cache_valid:
        return cached_value

    # Using "formatted=0" returns the times in a full datetime format
    # Otherwise you need to do some silly math to figure out the date
    # of the sunrise or sunset.
    url = "https://api.sunrise-sunset.org/json?lat=" + \
        str(__airport_locations__[airport_iaco_code]["lat"]) + \
        "&lng=" + str(__airport_locations__[airport_iaco_code]["long"]) + \
        "&date=" + str(utc_time.year) + "-" + str(utc_time.month) + "-" + str(utc_time.day) + \
        "&formatted=0"

    json_result = __rest_session__.get(url, timeout=2).json()

    if json_result is not None and "status" in json_result and json_result["status"] == "OK" and "results" in json_result:
        sunrise_and_sunet = (__get_utc_datetime__(
            json_result["results"]["sunrise"]), __get_utc_datetime__(json_result["results"]["sunset"]))
        __set_cache__(airport_iaco_code, __daylight_cache__, sunrise_and_sunet)

        return sunrise_and_sunet

    return None


def is_daylight(airport_iaco_code):
    """
    Returns TRUE if the airport is currently in daylight

    Arguments:
        airport_iaco_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in daylight.
    """

    light_times = get_civil_twilight(airport_iaco_code)

    if light_times is not None:
        utc_time = datetime.utcnow()

        return light_times[0] < utc_time and utc_time < light_times[1]

    return True


def get_metar(airport_iaco_code):
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_iaco_code {string} -- The IACO code for the weather station.

    Returns:
        string -- The RAW metar (if any) for the given station. Returns INVALID if
        and error occurs or the station does not exist.
    """

    is_cache_valid, cached_metar = __is_cache_valid__(
        airport_iaco_code, __metar_report_cache__)

    if is_cache_valid and cached_metar != INVALID:
        return cached_metar

    try:
        stream = urllib.urlopen('http://www.aviationweather.gov/metar/data?ids=' +
                                airport_iaco_code + '&format=raw&hours=0&taf=off&layout=off&date=0')
        for line in stream:
            if '<!-- Data starts here -->' in line:
                metar = re.sub('<[^<]+?>', '', stream.readline())
                __set_cache__(airport_iaco_code, __metar_report_cache__, metar)

                return metar
        return INVALID
    except Exception, e:
        print str(e)
        return INVALID
    finally:
        try:
            stream.close()
        except:
            print "Error closing stream"


def get_visibilty(metar):
    """
    Returns the flight rules classification based on visibility from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """

    match = re.search('( [0-9] )?([0-9]/?[0-9]?SM)', metar)
    if(match == None):
        return INVALID
    (g1, g2) = match.groups()
    if(g2 == None):
        return INVALID
    if(g1 != None):
        return IFR
    if '/' in g2:
        return LIFR
    vis = int(re.sub('SM', '', g2))
    if vis < 3:
        return IFR
    if vis <= 5:
        return MVFR
    return VFR


def get_ceiling(metar):
    """
    Returns the flight rules classification based on ceiling from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """

    components = metar.split(' ')
    minimum_ceiling = 10000
    for component in components:
        if 'BKN' in component or 'OVC' in component:
            ceiling = int(filter(str.isdigit, component)) * 100
            if(ceiling < minimum_ceiling):
                minimum_ceiling = ceiling
    return minimum_ceiling


def get_ceiling_category(ceiling):
    """
    Returns the flight rules classification based on the cloud ceiling.

    Arguments:
        ceiling {int} -- Number of feet the clouds are above the ground.

    Returns:
        string -- The flight rules classification.
    """

    if ceiling < 500:
        return LIFR
    if ceiling < 1000:
        return IFR
    if ceiling < 3000:
        return MVFR
    return VFR


def get_category(airport_iaco_code, metar, return_night):
    """
    Returns the flight rules classification based on the entire RAW metar.

    Arguments:
        airport_iaco_code -- The airport or weather station that we want to get a category for.
        metar {string} -- The RAW weather report in METAR format.
        return_night {boolean} -- Should we return a category for NIGHT?

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """
    try:
        if return_night and not is_daylight(airport_iaco_code):
            return NIGHT
    except:
        pass

    if metar == INVALID:
        return INVALID

    vis = get_visibilty(metar)
    ceiling = get_ceiling_category(get_ceiling(metar))
    if ceiling == INVALID:
        return INVALID
    if vis == LIFR or ceiling == LIFR:
        return LIFR
    if vis == IFR or ceiling == IFR:
        return IFR
    if vis == MVFR or ceiling == MVFR:
        return MVFR

    return VFR


if __name__ == '__main__':
    result = get_civil_twilight("KAWO")
    is_lit = is_daylight("KAWO")

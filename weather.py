"""
Handles fetching and decoding weather.
"""

import csv
import json
import os
import re
import urllib
from datetime import datetime, timedelta

import requests

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


def __load_airport_data__(working_directory=os.path.dirname(os.path.abspath(__file__)),
                          airport_data_file="./data/airports.csv"):
    """
    Loads all of the airport and weather station data from the included CSV file
    then places it into a dictionary for easy use.

    Keyword Arguments:
        airport_data_file {str} -- The file that contains the airports (default: {"./data/airports.csv"})

    Returns:
        dictionary -- A map of the airport data keyed by IACO code.
    """
    full_file_path = os.path.join(
        working_directory, os.path.normpath(airport_data_file))

    csvfile = open(full_file_path, 'r')

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


def __is_cache_valid__(airport_iaco_code, cache, cache_life_in_minutes=8):
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


def get_civil_twilight(airport_iaco_code, current_utc_time=None, use_cache=True):
    """
    Gets the civil twilight time for the given airport

    Arguments:
        airport_iaco_code {string} -- The IACO code of the airport.

    Returns:
        When civil sunrise and sunset are in UTC
    """

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    is_cache_valid, cached_value = __is_cache_valid__(
        airport_iaco_code, __daylight_cache__, 4 * 60)

    # Make sure that the sunrise time we are using is still valid...
    if is_cache_valid:
        hours_since_sunrise = (
            current_utc_time - cached_value[0]).total_seconds() / 3600
        if hours_since_sunrise > 24:
            is_cache_valid = False
            print("Twilight cache for {} had a HARD miss with delta={}".format(
                airport_iaco_code, hours_since_sunrise))

    if is_cache_valid and use_cache:
        return cached_value

    # Using "formatted=0" returns the times in a full datetime format
    # Otherwise you need to do some silly math to figure out the date
    # of the sunrise or sunset.
    url = "https://api.sunrise-sunset.org/json?lat=" + \
        str(__airport_locations__[airport_iaco_code]["lat"]) + \
        "&lng=" + str(__airport_locations__[airport_iaco_code]["long"]) + \
        "&date=" + str(current_utc_time.year) + "-" + str(current_utc_time.month) + "-" + str(current_utc_time.day) + \
        "&formatted=0"

    json_result = __rest_session__.get(url, timeout=2).json()

    if json_result is not None and "status" in json_result and json_result["status"] == "OK" and "results" in json_result:
        sunrise_and_sunet = (__get_utc_datetime__(
            json_result["results"]["sunrise"]), __get_utc_datetime__(json_result["results"]["sunset"]))
        __set_cache__(airport_iaco_code, __daylight_cache__, sunrise_and_sunet)

        return sunrise_and_sunet

    return None


def is_daylight(airport_iaco_code, current_utc_time=None, use_cache=True):
    """
    Returns TRUE if the airport is currently in daylight

    Arguments:
        airport_iaco_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in daylight.
    """

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    light_times = get_civil_twilight(
        airport_iaco_code, current_utc_time, use_cache)

    if light_times is not None:
        # Deal with day old data...
        hours_since_sunrise = (
            current_utc_time - light_times[0]).total_seconds() / 3600
        if hours_since_sunrise > 24:
            print("is_daylight had a hard miss with delta={}".format(
                hours_since_sunrise))
            return True

        return light_times[0] < current_utc_time and current_utc_time < light_times[1]

    return True


def extract_metar_from_html_line(metar):
    """
    Takes a raw line of HTML from the METAR report and extracts the METAR from it.
    NOTE: A "$" at the end of the line indicates a "maintainence check" and is part of the report.

    Arguments:
        metar {string} -- The raw HTML line that may include BReaks and other HTML elements.

    Returns:
        string -- The extracted METAR.
    """

    metar = metar.split('<')[0]
    metar = re.sub('<[^<]+?>', '', metar)
    metar = metar.replace('\n', '')
    metar = metar.strip()

    return metar


def get_metars(airport_iaco_codes):
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_iaco_codes {string} -- The list of IACO code for the weather station.

    Returns:
        dictionary - A dictionary (keyed by airport code) of the RAW metars.
        Returns INVALID as the value for the key if an error occurs.
    """

    metar_list = " ".join(airport_iaco_codes)
    metars = {}

    try:
        stream = urllib.urlopen(
            'https://www.aviationweather.gov/metar/data?ids={}&format=raw&hours=0&taf=off&layout=off&date=0'.format(metar_list))
        data_found = False
        stream_lines = stream.readlines()
        stream.close()
        for line in stream_lines:
            if '<!-- Data starts here -->' in line:
                data_found = True
                continue
            elif '<!-- Data ends here -->' in line:
                break
            elif data_found:
                metar = ''
                try:
                    metar = extract_metar_from_html_line(line)

                    if(len(metar) < 1):
                        continue

                    identifier = metar.split(' ')[0]
                    __set_cache__(identifier, __metar_report_cache__, metar)
                except:
                    metar = INVALID

                metars[identifier] = metar
    except Exception, e:
        print('EX:{}'.format(e))

    return metars


def get_metar(airport_iaco_code, use_cache=True):
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_iaco_code {string} -- The IACO code for the weather station.

    Keyword Arguments:
        use_cache {bool} -- Should we use the cache? Set to false to bypass the cache. (default: {True})
    """

    is_cache_valid, cached_metar = __is_cache_valid__(
        airport_iaco_code, __metar_report_cache__)

    if is_cache_valid and cached_metar != INVALID and use_cache:
        return cached_metar

    try:
        metars = get_metars([airport_iaco_code])

        if metars is None:
            return INVALID

        if airport_iaco_code not in metars:
            return INVALID

        return metars[airport_iaco_code]

    except Exception, e:
        print("EX:{}".format(e))

        return INVALID


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
    starting_date_time = datetime.utcnow()
    utc_offset = starting_date_time - datetime.now()

    metars = get_metars(['KAWO', 'KSEA'])
    get_metar('KAWO', False)

    for hours_ahead in range(0, 48):
        print('----')
        time_to_fetch = starting_date_time + timedelta(hours=hours_ahead)
        local_fetch_time = time_to_fetch - utc_offset

        print("UTC={}, LOCAL={}".format(time_to_fetch, local_fetch_time))

        for airport in ['KAWO', 'KCOE', 'KMSP', 'KOSH']:
            is_lit = is_daylight(airport, time_to_fetch)

            print("{}: is_lit={}".format(airport, is_lit))

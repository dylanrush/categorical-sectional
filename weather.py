"""
Handles fetching and decoding weather.
"""

import csv
import json
import os
import re
import urllib.request
import threading
from datetime import datetime, timedelta

import requests

INVALID = 'INVALID'
VFR = 'VFR'
MVFR = 'M' + VFR
IFR = 'IFR'
LIFR = 'L' + IFR
NIGHT = 'NIGHT'
SMOKE = 'SMOKE'

RED = 'RED'
GREEN = 'GREEN'
BLUE = 'BLUE'
GRAY = 'GRAY'
YELLOW = 'YELLOW'
DARK_YELLOW = 'DARK YELLOW'
WHITE = 'WHITE'
LOW = 'LOW'
OFF = 'OFF'

__light_fetch_lock__ = threading.Lock()
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

    csvfile = open(full_file_path, 'r', encoding='utf-8')

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
        An array that describes the following:
        0 - When sunrise starts
        1 - when sunrise is
        2 - when sunrise is finished
        3 - when sunset starts
        4 - when sunset is
        5 - when sunset is finished
    """

    __light_fetch_lock__.acquire()

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    is_cache_valid, cached_value = __is_cache_valid__(
        airport_iaco_code, __daylight_cache__, 4 * 60)

    # Make sure that the sunrise time we are using is still valid...
    if is_cache_valid:
        hours_since_sunrise = (
            current_utc_time - cached_value[1]).total_seconds() / 3600
        if hours_since_sunrise > 24:
            is_cache_valid = False
            print("Twilight cache for {} had a HARD miss with delta={}".format(
                airport_iaco_code, hours_since_sunrise))
            current_utc_time += timedelta(hours=1)

    if is_cache_valid and use_cache:
        __light_fetch_lock__.release()
        return cached_value

    # Using "formatted=0" returns the times in a full datetime format
    # Otherwise you need to do some silly math to figure out the date
    # of the sunrise or sunset.
    url = "https://api.sunrise-sunset.org/json?lat=" + \
        str(__airport_locations__[airport_iaco_code]["lat"]) + \
        "&lng=" + str(__airport_locations__[airport_iaco_code]["long"]) + \
        "&date=" + str(current_utc_time.year) + "-" + str(current_utc_time.month) + "-" + str(current_utc_time.day) + \
        "&formatted=0"

    json_result = []
    try:
        json_result = __rest_session__.get(url, timeout=2).json()
    except:
        return []

    if json_result is not None and "status" in json_result and json_result["status"] == "OK" and "results" in json_result:
        sunrise = __get_utc_datetime__(json_result["results"]["sunrise"])
        sunset = __get_utc_datetime__(json_result["results"]["sunset"])
        sunrise_start = __get_utc_datetime__(
            json_result["results"]["civil_twilight_begin"])
        sunset_end = __get_utc_datetime__(
            json_result["results"]["civil_twilight_end"])
        sunrise_length = sunrise - sunrise_start
        sunset_length = sunset_end - sunset
        avg_transition_time = timedelta(seconds=(sunrise_length.seconds +
                                                 sunset_length.seconds) / 2)
        sunrise_and_sunset = [sunrise - avg_transition_time,
                              sunrise,
                              sunrise + avg_transition_time,
                              sunset - avg_transition_time,
                              sunset,
                              sunset + avg_transition_time]
        __set_cache__(airport_iaco_code, __daylight_cache__,
                      sunrise_and_sunset)

        __light_fetch_lock__.release()
        return sunrise_and_sunset

    __light_fetch_lock__.release()
    return None


def is_daylight(airport_iaco_code, light_times, current_utc_time=None, use_cache=True):
    """
    Returns TRUE if the airport is currently in daylight

    Arguments:
        airport_iaco_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in daylight.
    """

    # print("------")

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    if light_times is not None and len(light_times) == 6:
        # Deal with day old data...
        hours_since_sunrise = (
            current_utc_time - light_times[1]).total_seconds() / 3600

        if hours_since_sunrise < 0:
            light_times = get_civil_twilight(
                airport_iaco_code, current_utc_time - timedelta(hours=24), False)

        if hours_since_sunrise > 24:
            return True

        # print("SUNRISE:{}".format(light_times[0]))
        # print("CURRENT:{}".format(current_utc_time))
        # print("SUNSET:{}".format(light_times[1]))

        # Make sure the time between takes into account
        # The amount of time sunrise or sunset takes
        is_after_sunrise = light_times[2] < current_utc_time
        is_before_sunset = current_utc_time < light_times[3]

        return is_after_sunrise and is_before_sunset

    return True


def is_night(airport_iaco_code, light_times, current_utc_time=None, use_cache=True):
    """
    Returns TRUE if the airport is currently in night

    Arguments:
        airport_iaco_code {string} -- The airport code to test.

    Returns:
        boolean -- True if the airport is currently in night.
    """

    # print("------")

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    if light_times is not None:
        # Deal with day old data...
        hours_since_sunrise = (
            current_utc_time - light_times[1]).total_seconds() / 3600

        if hours_since_sunrise < 0:
            light_times = get_civil_twilight(
                airport_iaco_code, current_utc_time - timedelta(hours=24), False)

        if hours_since_sunrise > 24:
            return False

        # print("SUNRISE:{}".format(light_times[0]))
        # print("CURRENT:{}".format(current_utc_time))
        # print("SUNSET:{}".format(light_times[1]))

        # Make sure the time between takes into account
        # The amount of time sunrise or sunset takes
        is_before_sunrise = current_utc_time < light_times[0]
        is_after_sunset = current_utc_time > light_times[5]

        return is_before_sunrise or is_after_sunset

    return False


def get_proportion_between_times(start, current, end):
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current time is.
    IE:
        If the CurrentTime is the same as StartTime, then the result will be 0.0
        If the CurrentTime is the same as the EndTime, then the result will be 1.0
        If the CurrentTime is halfway between StartTime and EndTime, then the result will be 0.5


    Arguments:
        start {datetime} -- The starting time.
        current {datetime} -- The time we want to get the proportion for.
        end {datetime} -- The end time to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End
    """

    total_delta = (end - start).total_seconds()
    time_in = (current - start).total_seconds()

    return time_in / total_delta


def get_twilight_transition(airport_iaco_code, current_utc_time=None, use_cache=True):
    """
    Returns the mix of dark & color fade for twilight transitions.

    Arguments:
        airport_iaco_code {string} -- The IACO code of the weather station.

    Keyword Arguments:
        current_utc_time {datetime} -- The time in UTC to calculate the mix for. (default: {None})
        use_cache {bool} -- Should the cache be used to determine the sunrise/sunset/transition data. (default: {True})

    Returns:
        tuple -- (proportion_off_to_night, proportion_night_to_category)
    """

    if current_utc_time is None:
        current_utc_time = datetime.utcnow()

    light_times = get_civil_twilight(
        airport_iaco_code, current_utc_time, use_cache)

    if light_times is None or len(light_times) < 5:
        return 0.0, 1.0

    if is_daylight(airport_iaco_code, light_times, current_utc_time, use_cache):
        return 0.0, 1.0

    if is_night(airport_iaco_code, light_times, current_utc_time, use_cache):
        return 0.0, 0.0

    proportion_off_to_night = 0.0
    proportion_night_to_color = 0.0

    # Sunsetting: Night to off
    if current_utc_time >= light_times[4]:
        proportion_off_to_night = 1.0 - \
            get_proportion_between_times(
                light_times[4], current_utc_time, light_times[5])
    # Sunsetting: Color to night
    elif current_utc_time >= light_times[3]:
        proportion_night_to_color = 1.0 - \
            get_proportion_between_times(
                light_times[3], current_utc_time, light_times[4])
    # Sunrising: Night to color
    elif current_utc_time >= light_times[1]:
        proportion_night_to_color = get_proportion_between_times(
            light_times[1], current_utc_time, light_times[2])
    # Sunrising: off to night
    else:
        proportion_off_to_night = get_proportion_between_times(
            light_times[0], current_utc_time, light_times[1])

    return proportion_off_to_night, proportion_night_to_color


def extract_metar_from_html_line(raw_metar_line):
    """
    Takes a raw line of HTML from the METAR report and extracts the METAR from it.
    NOTE: A "$" at the end of the line indicates a "maintainence check" and is part of the report.

    Arguments:
        metar {string} -- The raw HTML line that may include BReaks and other HTML elements.

    Returns:
        string -- The extracted METAR.
    """

    metar = re.sub('<[^<]+?>', '', raw_metar_line)
    metar = metar.replace('\n', '')
    metar = metar.strip()

    return metar


def get_metar_from_report_line(metar_report_line_from_webpage):
    """
    Extracts the METAR from the line in the webpage and sets
    the data into the cache.

    Returns None if an error occurs or nothing can be found.

    Arguments:
        metar_report_line_from_webpage {string} -- The line that contains the METAR from the web report.

    Returns:
        string,string -- The identifier and extracted METAR (if any), or None
    """

    identifier = None
    metar = None

    try:
        metar = extract_metar_from_html_line(metar_report_line_from_webpage)

        if len(metar) < 1:
            return (None, None)

        identifier = metar.split(' ')[0]
        __set_cache__(identifier, __metar_report_cache__, metar)
    except:
        metar = None

    return (identifier, metar)


def get_metars(airport_iaco_codes):
    """
    Returns the (RAW) METAR for the given station

    Arguments:
        airport_iaco_codes {string} -- The list of IACO code for the weather station.

    Returns:
        dictionary - A dictionary (keyed by airport code) of the RAW metars.
        Returns INVALID as the value for the key if an error occurs.
    """

    metars = {}

    try:
        metars = get_metar_reports_from_web(airport_iaco_codes)

    except Exception as e:
        print('EX:{}'.format(e))
        metars = {}

    # For the airports and identifiers that we were not able to get
    # a result for, see if we can fill in the results.
    for identifier in airport_iaco_codes:
        if identifier in metars and metars[identifier] is not None:
            continue

        # If we did not get a report, but do
        # still have an old report, then use the old
        # report.
        if identifier in __metar_report_cache__:
            metars[identifier] = __metar_report_cache__[identifier]
        # Fall back to an "INVALID" if everything else failed.
        else:
            metars[identifier] = INVALID

    return metars


def get_metar_reports_from_web(airport_iaco_codes):
    """
    Calls to the web an attempts to gets the METARs for the requested station list.

    Arguments:
        airport_iaco_codes {string[]} -- Array of stations to get METARs for.

    Returns:
        dictionary -- Returns a map of METARs keyed by the station code.
    """

    metars = {}
    metar_list = "%20".join(airport_iaco_codes)
    request_url = 'https://www.aviationweather.gov/metar/data?ids={}&format=raw&hours=0&taf=off&layout=off&date=0'.format(
        metar_list)
    stream = urllib.request.urlopen(request_url, timeout=2)
    data_found = False
    stream_lines = stream.readlines()
    stream.close()
    for line in stream_lines:
        line_as_string = line.decode("utf-8")
        if '<!-- Data starts here -->' in line_as_string:
            data_found = True
            continue
        elif '<!-- Data ends here -->' in line_as_string:
            break
        elif data_found:
            identifier, metar = get_metar_from_report_line(line_as_string)

            if identifier is None:
                continue

            # If we get a good report, go ahead and shove it into the results.
            if metar is not None:
                metars[identifier] = metar

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
            return None

        if airport_iaco_code not in metars:
            return None

        return metars[airport_iaco_code]

    except Exception as e:
        print("EX:{}".format(e))

        return None


def get_metar_age(metar):
    """
    Returns the age of the METAR

    Arguments:
        metar {string} -- The METAR to get the age from.

    Returns:
        timedelta -- The age of the metar, None if it can not be determined.
    """

    try:
        current_time = datetime.utcnow()
        embedded_dates = re.search(r'^\w{4}\s(.{6})Z', metar)
        metar_date = current_time - timedelta(days=31)

        if embedded_dates is not None:
            partial_date_time = embedded_dates[0].split(' ')[1].split('Z')[0]
            day_number = int(partial_date_time[:2])
            hour = int(partial_date_time[2:4])
            minute = int(partial_date_time[4:6])

            metar_date = datetime(
                current_time.year, current_time.month, current_time.day, hour, minute)

            # Assume that the report is from the past, and work backwards.
            days_back = 0
            while metar_date.day != day_number and days_back <= 31:
                metar_date -= timedelta(days=1)
                days_back += 1           
        
        return current_time - metar_date
    except:
        return None


def get_visibilty(metar):
    """
    Returns the flight rules classification based on visibility from a RAW metar.

    Arguments:
        metar {string} -- The RAW weather report in METAR format.

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """

    match = re.search('( [0-9] )?([0-9]/?[0-9]?SM)', metar)
    is_smoke = re.search('.* FU .*', metar) is not None
    if(match == None):
        return INVALID
    (g1, g2) = match.groups()
    if(g2 == None):
        return INVALID
    if(g1 != None):
        if is_smoke:
            return SMOKE
        return IFR
    if '/' in g2:
        if is_smoke:
            return SMOKE
        return LIFR
    vis = int(re.sub('SM', '', g2))
    if vis < 3:
        if is_smoke:
            return SMOKE
        return IFR
    if vis <= 5:
        if is_smoke:
            return SMOKE

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
            ceiling = int(''.join(filter(str.isdigit, component))) * 100
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


def get_category(airport_iaco_code, metar):
    """
    Returns the flight rules classification based on the entire RAW metar.

    Arguments:
        airport_iaco_code -- The airport or weather station that we want to get a category for.
        metar {string} -- The RAW weather report in METAR format.
        return_night {boolean} -- Should we return a category for NIGHT?

    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """
    if metar is None or metar == INVALID:
        return INVALID

    # metar_age = get_metar_age(metar)
    #
    # # Allow the metar to "age out" if we have not had a report for a while.
    # if metar_age is None:
    #     print('No METAR available in AGE CHECK - returning INVALID')
    #     return INVALID
    # elif (metar_age.total_seconds() / 60.0) > 60.0:
    #     print('Aging out METAR due to an age of {:.1} minutes - returning INVALID'.format(metar_age.total_seconds() / 60.0))
    #     return INVALID

    metar_age = get_metar_age(metar)

    print("{} - Issued {:.1f} minutes ago".format(airport_iaco_code, metar_age.total_seconds() / 60))

    vis = get_visibilty(metar)
    ceiling = get_ceiling_category(get_ceiling(metar))
    if ceiling == INVALID or vis == INVALID:
        return INVALID
    if vis == SMOKE:
        return SMOKE
    if vis == LIFR or ceiling == LIFR:
        return LIFR
    if vis == IFR or ceiling == IFR:
        return IFR
    if vis == MVFR or ceiling == MVFR:
        return MVFR

    return VFR


if __name__ == '__main__':
    airports_to_test = ['KAWO', 'KOSH', 'KBVS', 'KDOESNTEXIST']
    starting_date_time = datetime.utcnow()
    utc_offset = starting_date_time - datetime.now()

    metars = get_metars(airports_to_test)
    get_metar('KAWO', False)

    for identifier in airports_to_test:
        metar = get_metar(identifier)
        age = get_metar_age(metar)
        flight_category = get_category(identifier, metar)
        print('{}: {}: {}'.format(identifier, flight_category, metar))

    for hours_ahead in range(0, 240):
        hours_ahead *= 0.1
        time_to_fetch = starting_date_time + timedelta(hours=hours_ahead)
        local_fetch_time = time_to_fetch - utc_offset

        for airport in ['KAWO']:  # , 'KCOE', 'KMSP', 'KOSH']:
            light_times = get_civil_twilight(airport, time_to_fetch)
            is_lit = is_daylight(airport, light_times, time_to_fetch)
            is_dark = is_night(airport, light_times, time_to_fetch)
            transition = get_twilight_transition(airport, time_to_fetch)

            print("DELTA=+{0:.1f}, LOCAL={1}, AIRPORT={2}: is_day={3}, is_night={4}, p_dark:{5:.1f}, p_color:{6:.1f}".format(
                hours_ahead, local_fetch_time, airport, is_lit, is_dark, transition[0], transition[1]))

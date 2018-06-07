"""
Handles fetching and decoding weather.
"""

import re
import urllib

INVALID = 'INVALID'
VFR = 'VFR'
MVFR = 'M' + VFR
IFR = 'IFR'
LIFR = 'L' + IFR

RED = 'RED'
GREEN = 'GREEN'
BLUE = 'BLUE'
LOW = 'LOW'
OFF = 'OFF'


def get_metar(airport_iaco_code):
    """
    Returns the (RAW) METAR for the given station
    
    Arguments:
        airport_iaco_code {string} -- The IACO code for the weather station.
    
    Returns:
        string -- The RAW metar (if any) for the given station. Returns INVALID if
        and error occurs or the station does not exist.
    """

    try:
        stream = urllib.urlopen('http://www.aviationweather.gov/metar/data?ids=' +
                                airport_iaco_code + '&format=raw&hours=0&taf=off&layout=off&date=0')
        for line in stream:
            if '<!-- Data starts here -->' in line:
                return re.sub('<[^<]+?>', '', stream.readline())
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


def get_category(metar):
    """
    Returns the flight rules classification based on the entire RAW metar.
    
    Arguments:
        metar {string} -- The RAW weather report in METAR format.
    
    Returns:
        string -- The flight rules classification, or INVALID in case of an error.
    """
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

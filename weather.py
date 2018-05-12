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


def get_metar(airport_iaco_code):
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
        stream.close()


def get_visibilty(metar):
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
    components = metar.split(' ')
    minimum_ceiling = 10000
    for component in components:
        if 'BKN' in component or 'OVC' in component:
            ceiling = int(filter(str.isdigit, component)) * 100
            if(ceiling < minimum_ceiling):
                minimum_ceiling = ceiling
    return minimum_ceiling


def get_ceiling_category(ceiling):
    if ceiling < 500:
        return LIFR
    if ceiling < 1000:
        return IFR
    if ceiling < 3000:
        return MVFR
    return VFR


def get_category(metar):
    vis = get_visibilty(metar)
    ceiling = get_ceiling_category(get_ceiling(metar))
    if(ceiling == INVALID):
        return INVALID
    if(vis == LIFR or ceiling == LIFR):
        return LIFR
    if(vis == IFR or ceiling == IFR):
        return IFR
    if(vis == MVFR or ceiling == MVFR):
        return MVFR
    return VFR

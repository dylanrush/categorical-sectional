import urllib,re
def get_metar(airport):
  try:
    stream = urllib.urlopen('http://www.aviationweather.gov/metar/data?ids='+airport+'&format=raw&hours=0&taf=off&layout=off&date=0');
    for line in stream:
      if '<!-- Data starts here -->' in line:
        return re.sub('<[^<]+?>', '', stream.readline())
    return 'INVALID'
  except Exception, e:
    print str(e);
    return 'INVALID'
  finally:
    stream.close();
def get_vis(metar):
  components = metar.split(' ');
  for component in components:
    if 'SM' in component:
      return re.sub('SM', '', component)
  return 'INVALID'
def get_vis_category(vis):
  if '/' in vis:
    return 'LIFR'
  vis_int = int(vis)
  if vis < 3:
    return 'IFR'
  if vis <= 5:
    return 'MVFR'
  return 'VFR'
def get_ceiling(metar):
  components = metar.split(' ' );
  minimum_ceiling = 10000
  for component in components:
    if 'BKN' in component or 'OVC' in component:
      ceiling = int(filter(str.isdigit,component)) * 100
      if(ceiling < minimum_ceiling):
        minimum_ceiling = ceiling
  return minimum_ceiling
def get_ceiling_category(ceiling):
  if ceiling < 500:
    return 'LIFR'
  if ceiling < 1000:
    return 'IFR'
  if ceiling < 3000:
    return 'MVFR'
  return 'VFR'
def get_category(metar):
  vis = get_vis_category(get_vis(metar))
  ceiling = get_ceiling_category(get_ceiling(metar))
  if(vis == 'INVALID' or ceiling == 'INVALID')
    return 'INVALID'
  if(vis == 'LIFR' or ceiling == 'LIFR')
    return 'LIFR'
  if(vis == 'IFR' or ceiling == 'IFR')
    return 'IFR'
  if(vis == 'MVFR' or ceiling == 'MVFR')
    return 'MVFR'
  return 'VFR'

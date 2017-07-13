import urllib
def get_metar(airport):
  stream = urllib.urlopen("http://www.aviationweather.gov/metar/data?ids="+airport+"&format=raw&hours=0&taf=off&layout=off&date=0");
  for line in stream:
    print line
  stream.close();

get_metar('KRNT')

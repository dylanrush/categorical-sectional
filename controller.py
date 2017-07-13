import RPi.GPIO as GPIO
import time
import urllib
import re
from threading import Thread

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
  if(vis == 'INVALID' or ceiling == 'INVALID'):
    return 'INVALID'
  if(vis == 'LIFR' or ceiling == 'LIFR'):
    return 'LIFR'
  if(vis == 'IFR' or ceiling == 'IFR'):
    return 'IFR'
  if(vis == 'MVFR' or ceiling == 'MVFR'):
    return 'MVFR'
  return 'VFR'

airport_pins = {'KRNT':(3,5,7),
        'KSEA':(11,13,15),
        'KPLU':(19,21,23),
        'KOLM':(29,31,33),
        'KTIW':(32,35,37),
        'KPWT':(36,38,40),
        'KSHN':(8,10,12)}

colors = {'RED':(GPIO.HIGH, GPIO.LOW, GPIO.LOW),
'GREEN':(GPIO.LOW, GPIO.HIGH, GPIO.LOW),
'BLUE':(GPIO.LOW, GPIO.LOW, GPIO.HIGH),
'LOW':(GPIO.LOW, GPIO.LOW, GPIO.LOW)}

airport_flasher = True
airport_should_flash = {}
airport_color = {}

for airport in airport_pins:
  airport_should_flash[airport] = True
  airport_color[airport] = 'BLUE'

def set_airport_display(airport, category):
  if category == 'VFR':
    airport_should_flash[airport] = False
    airport_color[airport] = 'GREEN'
  elif category == 'MVFR':
    airport_should_flash[airport] = False
    airport_color[airport] = 'BLUE'
  elif category == 'IFR':
    airport_should_flash[airport] = False
    airport_color[airport] = 'RED'
  elif category == 'LIFR':
    airport_should_flash[airport] = True
    airport_color[airport] = 'RED'
  else:
    airport_should_flash[airport] = True
    airport_color[airport] = 'BLUE'

def refresh_airport_displays():
  for airport in airport_pins:
    category = get_category(get_metar(airport))
    set_airport_display(airport, category)

def render_airport_displays():
  for airport in airport_pins:
    if airport_should_flash[airport] and airport_flasher == True:
      setLed(airport_pins[airport], 'LOW')
    else:
      setLed(airport_pins[airport], airport_color[airport])
  airport_flasher = bool(not airport_flasher)

#VFR - Green
#MVFR - Blue
#IFR - Red
#LIFR - Flashing red
#Error - Flashing blue



def setLed(pins, color):
  GPIO.output(pins, colors[color])
def all_airports(color):
  for airport in airport_pins:
    print str(airport_pins[airport])
    GPIO.setup(airport_pins[airport], GPIO.OUT)
    setLed(airport_pins[airport], color)

def render_thread():
  while(True):
    render_airport_displays
    time.sleep(1)

def refresh_thread():
  while(True):
    refresh_airport_displays
    time.sleep(60)



GPIO.setmode(GPIO.BOARD)
# Test LEDS on startup
all_airports('GREEN')

time.sleep(2)

all_airports('LOW')

time.sleep(2)

all_airports('GREEN')

time.sleep(2)

thread1 = Thread(target = render_thread)
thread2 = Thread(target = refresh_thread)
thread1.start()
thread2.start()

thread1.join()
thread2.join()

GPIO.cleanup()


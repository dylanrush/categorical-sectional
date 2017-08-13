# Live Sectional Map controller
# Dylan Rush 2017
# dylanhrush.com
# Uses RPi.GPIO library: https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/

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
  match = re.search('( [0-9] )?([0-9]/?[0-9]?SM)', metar)
  if(match == None):
    return 'INVAILD'
  (g1, g2) = match.groups()
  if(g2 == None):
    return 'INVALID'
  if(g1 != None):
    return 'IFR'
  if '/' in g2:
    return 'LIFR'
  vis = int(re.sub('SM','',g2))
  if vis < 3:
    return 'IFR'
  if vis <=5 :
    return 'MVFR'
  return 'VFR'

#def get_vis_category(vis):
#  if vis == 'INVALID':
#    return 'INVALID'
#  if '/' in vis:
#    return 'LIFR'
#  vis_int = int(vis)
#  if vis < 3:
#    return 'IFR'
#  if vis <= 5:
#    return 'MVFR'
#  return 'VFR'
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
  vis = get_vis(metar)
  ceiling = get_ceiling_category(get_ceiling(metar))
  if(ceiling == 'INVALID'):
    return 'INVALID'
  if(vis == 'LIFR' or ceiling == 'LIFR'):
    return 'LIFR'
  if(vis == 'IFR' or ceiling == 'IFR'):
    return 'IFR'
  if(vis == 'MVFR' or ceiling == 'MVFR'):
    return 'MVFR'
  return 'VFR'
GPIO.setmode(GPIO.BOARD)
airport_pins = {'KRNT':(3,5,7),
        'KSEA':(11,13,15),
        'KPLU':(19,21,23),
        'KOLM':(29,31,33),
        'KTIW':(32,35,37),
        'KPWT':(36,38,40),
        'KSHN':(8,10,12)}
for airport in airport_pins:
  GPIO.setup(airport_pins[airport], GPIO.OUT)  

pwm_frequency = 100.0

airport_pwm_matrix = {}
for airport in airport_pins:
  (redPin, greenPin, bluePin) = airport_pins[airport]
  airport_pwm_matrix[airport] = {}
  airport_pwm_matrix[airport]['RED'] = GPIO.PWM(redPin, pwm_frequency)
  airport_pwm_matrix[airport]['GREEN'] = GPIO.PWM(greenPin, pwm_frequency)
  airport_pwm_matrix[airport]['BLUE'] = GPIO.PWM(bluePin, pwm_frequency)
  for color in airport_pwm_matrix[airport]:
    airport_pwm_matrix[airport][color].start(0.0)

# Overrides can be used to test different conditions
overrides = {}
#overrides = {'KOLM':'IFR',
#             'KTIW':'MVFR',
#             'KPWT':'INVALID',
#             'KRNT':'LIFR'}


colors = {'RED':(20.0,0.0,0.0),
          'GREEN':(0.0,50.0,0.0),
          'BLUE':(0.0,0.0,100.0),
          'LOW':(0.0,0.0,0.0)}

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
    print "Retrieving METAR for "+airport
    metar = get_metar(airport)
    print "METAR for "+airport+" = "+metar
    category = get_category(metar)
    if airport in overrides:
      category = overrides[airport]
    print "Category for "+airport+" = "+category
    set_airport_display(airport, category)

def setLed(airport, color):
  airport_pwm_matrix[airport]['RED'].ChangeDutyCycle(colors[color][0])
  airport_pwm_matrix[airport]['GREEN'].ChangeDutyCycle(colors[color][1])
  airport_pwm_matrix[airport]['BLUE'].ChangeDutyCycle(colors[color][2])

def render_airport_displays(airport_flasher):
  for airport in airport_pins:
    if airport_should_flash[airport] and airport_flasher:
      setLed(airport, 'LOW')
    else:
      setLed(airport, airport_color[airport])

#VFR - Green
#MVFR - Blue
#IFR - Red
#LIFR - Flashing red
#Error - Flashing blue

def all_airports(color):
  for airport in airport_pins:
    print str(airport_pins[airport])
    setLed(airport, color)

endtime = int(time.time()) + 14400

def render_thread():
  print "Starting rendering thread"
  while(time.time() < endtime):
    print "render"
    render_airport_displays(True)
    time.sleep(1)
    render_airport_displays(False)
    time.sleep(1)

def refresh_thread():
  print "Starting refresh thread"
  while(time.time() < endtime):
    print "Refreshing categories"
    refresh_airport_displays()
    time.sleep(60)

# Test LEDS on startup
all_airports('GREEN')

time.sleep(2)

all_airports('LOW')

time.sleep(2)

thread1 = Thread(target = render_thread)
thread2 = Thread(target = refresh_thread)
thread1.start()
thread2.start()

thread1.join()
thread2.join()

GPIO.cleanup()


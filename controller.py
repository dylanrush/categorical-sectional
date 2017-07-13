import RPi.GPIO as GPIO
import time
import urllib

airport_pins = {'KRNT':(3,5,7),
        'KSEA':(11,13,15),
        'KPLU':(19,21,23),
        'KOLM':(29,31,33),
        'KTIW':(32,35,37),
        'KPWT':(36,38,40),
        'KSHN':(8,10,12)}

colors = {'RED':(GPIO.HIGH, GPIO.LOW, GPIO.LOW),
'GREEN':(GPIO.LOW, GPIO.HIGH, GPIO.LOW),
'BLUE':(GPIO.LOW, GPIO.LOW, GPIO.HIGH)}

def setLed(pins, color):
  GPIO.output(pins, colors[color])
def all_airports(color):
  for airport in airport_pins:
    print str(airport_pins[airport])
    GPIO.setup(airport_pins[airport], GPIO.OUT)
    setLed(airport_pins[airport], color)



GPIO.setmode(GPIO.BOARD)

all_airports('RED')

time.sleep(5)

all_airports('GREEN')

time.sleep(5)

all_airports('BLUE')

time.sleep(5)

GPIO.cleanup()


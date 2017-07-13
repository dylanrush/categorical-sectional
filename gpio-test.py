import RPi.GPIO as GPIO
import time
import urllib
GPIO.setmode(GPIO.BCM)

GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)

time.sleep(5)

GPIO.cleanup()

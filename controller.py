# Live Sectional Map controller
# Dylan Rush 2017
# Additional modifications:
#   2018, John Marzulli
# dylanhrush.com
# Uses RPi.GPIO library: https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
# Free for personal use. Prohibited for commercial without consent

import time
import urllib
import re
import json
from threading import Thread
import lib.local_debug as local_debug
from lib.recurring_task import RecurringTask
import weather
import configuration

if local_debug.is_debug():
    from lib.local_debug import PWM
else:
    import RPi.GPIO as GPIO
    from RPi.GPIO import PWM


GPIO_DATA_FILE = "data/south_sound.json"


if not local_debug.is_debug():
    GPIO.setmode(GPIO.BOARD)

airport_pins = configuration.load_gpio_airport_pins(GPIO_DATA_FILE)

for airport in airport_pins:
    if local_debug.is_debug():
        print 'Would have set the GPIO pins as ' + airport + ':(' + str(airport_pins[airport][0]) + ',' + str(airport_pins[airport][1]) + ',' + str(airport_pins[airport][2]) + ')'
    else:
        GPIO.setup(airport_pins[airport], GPIO.OUT)

pwm_frequency = 100.0

airport_pwm_matrix = {}
for airport in airport_pins:
    (redPin, greenPin, bluePin) = airport_pins[airport]
    airport_pwm_matrix[airport] = {}
    airport_pwm_matrix[airport][weather.RED] = PWM(redPin, pwm_frequency)
    airport_pwm_matrix[airport][weather.GREEN] = PWM(greenPin, pwm_frequency)
    airport_pwm_matrix[airport][weather.BLUE] = PWM(bluePin, pwm_frequency)
    for color in airport_pwm_matrix[airport]:
        airport_pwm_matrix[airport][color].start(0.0)

# Overrides can be used to test different conditions
overrides = configuration.get_overrides()


colors = configuration.get_colors()
if configuration.MODE is configuration.PWM:
    colors = configuration.get_pwm_colors()

airport_should_flash = {}
airport_color = {}

for airport in airport_pins:
    airport_should_flash[airport] = True
    airport_color[airport] = weather.BLUE


def set_airport_display(airport, category):
    if category == weather.VFR:
        airport_should_flash[airport] = False
        airport_color[airport] = weather.GREEN
    elif category == weather.MVFR:
        airport_should_flash[airport] = False
        airport_color[airport] = weather.BLUE
    elif category == weather.IFR:
        airport_should_flash[airport] = False
        airport_color[airport] = weather.RED
    elif category == weather.LIFR:
        airport_should_flash[airport] = True
        airport_color[airport] = weather.RED
    else:
        airport_should_flash[airport] = True
        airport_color[airport] = weather.BLUE


def refresh_airport_displays():
    for airport in airport_pins:
        print "Retrieving METAR for " + airport
        metar = weather.get_metar(airport)
        print "METAR for " + airport + " = " + metar
        category = weather.get_category(metar)
        if airport in overrides:
            category = overrides[airport]
        print "Category for " + airport + " = " + category
        set_airport_display(airport, category)

def set_led(airport, color):
    if configuration.MODE is configuration.PWM:
        set_led_pwm(airport, color)
    else:
        set_led_normal(airport, color)

def set_led_normal(pins, color):
    if not local_debug.is_debug():
        GPIO.setup(pins, GPIO.OUT)
        GPIO.output(pins, colors[color])

def set_led_pwm(airport, color):
    airport_pwm_matrix[airport][weather.RED].ChangeDutyCycle(colors[color][0])
    airport_pwm_matrix[airport][weather.GREEN].ChangeDutyCycle(
        colors[color][1])
    airport_pwm_matrix[airport][weather.BLUE].ChangeDutyCycle(colors[color][2])


def render_airport_displays(airport_flasher):
    for airport in airport_pins:
        if airport_should_flash[airport] and airport_flasher:
            set_led(airport, weather.LOW)
        else:
            set_led(airport, airport_color[airport])

#VFR - Green
#MVFR - Blue
#IFR - Red
# LIFR - Flashing red
# Error - Flashing blue


def all_airports(color):
    for airport in airport_pins:
        print str(airport_pins[airport])
        set_led(airport, color)


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


if __name__ == '__main__':
    # Test LEDS on startup
    all_airports(weather.GREEN)

    time.sleep(2)

    all_airports(weather.LOW)

    time.sleep(2)

    render_task = RecurringTask('Render', 0, render_thread, None, True)
    refresh_task = RecurringTask('Refresh', 0, refresh_thread, None, True)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt, SystemExit:
            break

    if not local_debug.is_debug():
        GPIO.cleanup()

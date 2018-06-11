# Live Sectional Map controller
# Dylan Rush 2017
# Additional modifications:
#   2018, John Marzulli
# dylanhrush.com
# Uses RPi.GPIO library: https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/
# Free for personal use. Prohibited for commercial without consent
#
# pip install Adafruit-GPIO
# pip install RPi-GPIO
# pip install pytest
# pip install Adafruit_WS2801
#
# Raspberry Pi
# Run 'raspi-config' and enable the SPI bus under Advanced
#
# Wiring the WS2801 :
# https://learn.adafruit.com/12mm-led-pixels/wiring
# https://tutorials-raspberrypi.com/how-to-control-a-raspberry-pi-ws2801-rgb-led-strip/
# Blue -> 5V Minus AND Pi GND (Physical Pi 25)
# Red -> 5V Plus
# Yellow -> Pin 19(Physical)/SPI MOSI
# Green -> Pin 23(Physical)/SCLK/SPI
#


import time
import urllib
import re
import json
from threading import Thread
import lib.local_debug as local_debug
from lib.recurring_task import RecurringTask
from renderers import ws2801
from renderers import led
from renderers import led_pwm
import weather
import configuration

airport_conditions = {}


if local_debug.is_debug():
    from lib.local_debug import PWM
else:
    import RPi.GPIO as GPIO
    from RPi.GPIO import PWM

if not local_debug.is_debug():
    GPIO.setmode(GPIO.BOARD)

airport_render_config = configuration.get_airport_configs()
colors = configuration.get_colors()
color_by_rules = {
    weather.IFR: colors[weather.RED],
    weather.VFR: colors[weather.GREEN],
    weather.MVFR: colors[weather.BLUE],
    weather.LIFR: colors[weather.LOW],
    weather.NIGHT: colors[weather.YELLOW],
    weather.INVALID: colors[weather.BLUE]
}


def get_renderer():
    """
    Returns the renderer to use based on the type of
    LED lights given in the config.

    Returns:
        renderer -- Object that takes the colors and airport config and
        sets the LEDs.
    """

    if configuration.get_mode() == configuration.WS2801:
        pixel_count = configuration.CONFIG["pixel_count"]
        spi_port = configuration.CONFIG["spi_port"]
        spi_device = configuration.CONFIG["spi_device"]
        return ws2801.Ws2801Renderer(pixel_count, spi_port, spi_device)
    elif configuration.get_mode() == configuration.PWM:
        return led_pwm.LedPwmRenderer(airport_render_config)
    else:
        # "Normal" LEDs
        return led.LedRenderer(airport_render_config)

    return None


renderer = get_renderer()

for airport in airport_render_config:
    airport_conditions[airport] = (weather.MVFR, True)


def get_color_from_condition(category):
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [tuple] -- The color (also a tuple) and if it should blink.
    """

    if category == weather.VFR:
        return (weather.GREEN, False)
    elif category == weather.MVFR:
        return (weather.BLUE, False)
    elif category == weather.IFR:
        return (weather.RED, False)
    elif category == weather.LIFR:
        return (weather.RED, True)

    return (weather.BLUE, True)


def set_airport_display(airport, category):
    color_and_flash = get_color_from_condition(category)
    should_flash = color_and_flash[1]

    airport_conditions[airport] = (category, should_flash)


def refresh_station_weather():
    """
    Attempts to get the latest weather for all stations and
    categorize the reports.
    """

    for airport in airport_render_config:
        print "Retrieving METAR for " + airport
        metar = weather.get_metar(airport, configuration.get_night_lights())

        print "METAR for " + airport + " = " + metar
        category = weather.get_category(metar)

        print "Category for " + airport + " = " + category
        set_airport_display(airport, category)


def render_airport_displays(airport_flasher):
    for airport in airport_render_config:
        try:
            color_to_render = color_by_rules[airport_conditions[airport][0]]
            if airport_conditions[airport][1] and airport_flasher:
                color_to_render = colors[weather.OFF]

            renderer.set_led(airport_render_config[airport], color_to_render)
        except:
            print "Error attempting to render " + airport

#VFR - Green
#MVFR - Blue
#IFR - Red
# LIFR - Flashing red
# Error - Flashing blue


def all_airports(color):
    """
    Sets all of the airports to the given color

    Arguments:
        color {triple} -- Three integer tuple(triple?) of the RGB values
        of the color to set for ALL airports.
    """

    for airport in airport_render_config:
        airport_render_data = airport_render_config[airport]
        renderer.set_led(airport_render_data, colors[color])


def render_thread():
    print "Starting rendering thread"
    while True:
        try:
            render_airport_displays(True)
            time.sleep(1)
            render_airport_displays(False)
        except KeyboardInterrupt:
            quit()
        finally:
            time.sleep(1)


def refresh_thread():
    """
    Helper to refresh the weather from all of the stations.
    """

    print "Starting refresh thread"
    while True:
        try:
            print "Refreshing categories"
            refresh_station_weather()
        except KeyboardInterrupt:
            quit()
        finally:
            time.sleep(60)


if __name__ == '__main__':
    # Test LEDS on startup
    colors_to_init = (
        weather.LOW,
        weather.GRAY,
        weather.RED,
        weather.BLUE,
        weather.GREEN,
        weather.YELLOW,
        weather.OFF
    )

    for color in colors_to_init:
        print "Setting to " + color
        all_airports(color)
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

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


from datetime import datetime
import json
import logging
import logging.handlers
import re
import time
import urllib
import threading

import configuration
import lib.local_debug as local_debug
import weather
from lib.logger import Logger
from lib.recurring_task import RecurringTask
from renderers import led, led_pwm, ws2801

airport_conditions = {}
python_logger = logging.getLogger("weathermap")
python_logger.setLevel(logging.DEBUG)
LOGGER = Logger(python_logger)
HANDLER = logging.handlers.RotatingFileHandler(
    "weathermap.log", maxBytes=10485760, backupCount=10)
HANDLER.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
python_logger.addHandler(HANDLER)

thread_lock_object = threading.Lock()


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
    weather.INVALID: colors[weather.WHITE]
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
        # Only blink for normal LEDs.
        # PWM and WS2801 have their own color.
        return (weather.LOW, configuration.get_mode() == configuration.STANDARD)
    elif category == weather.NIGHT:
        return (weather.YELLOW, False)

    # Error
    return (weather.WHITE, True)


def set_airport_display(airport, category):
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """

    changed = False
    try:
        color_and_flash = get_color_from_condition(category)
        should_flash = color_and_flash[1]

        thread_lock_object.acquire()

        if airport in airport_conditions:
            changed = airport_conditions[airport][0] != category
        else:
            changed = True

        airport_conditions[airport] = (category, should_flash)
    finally:
        thread_lock_object.release()

    if changed:
        LOGGER.log_info_message(airport + " now " + category)

    return changed


def update_weather_for_all_stations():
    """
    Updates the weather for all of the stations.
    This does not update the conditions or category.
    """

    weather.get_metars(airport_render_config.keys())


def update_all_station_categorizations():
    """
    Takes the latest reports (probably in cache) and then
    updates the categorization of the airports.
    """

    utc_offset = datetime.utcnow() - datetime.now()

    for airport in airport_render_config:
        LOGGER.log_info_message("Retrieving METAR for " + airport)
        metar = weather.get_metar(airport)

        LOGGER.log_info_message("METAR for " + airport + " = " + metar)
        category = weather.INVALID

        try:
            category = weather.get_category(
                airport, metar, configuration.get_night_lights())
            twilight = weather.get_civil_twilight(airport)
            LOGGER.log_info_message("{} - Rise(UTC):{}, Set(UTC):{}".format(airport, twilight[0], twilight[1]))
            LOGGER.log_info_message("{} - Rise(HERE):{}, Set(HERE):{}".format(airport, twilight[0] - utc_offset, twilight[1] - utc_offset))
        except Exception as e:
            LOGGER.log_warning_message("Exception while attempting to categorize. EX:{}".format(e))

        LOGGER.log_info_message("Category for " + airport + " = " + category)
        set_airport_display(airport, category)


def get_airport_condition(airport):
    """
    Safely get the conditions at an airport

    Arguments:
        airport {str} -- The airport identifier

    Returns:
        tuple -- condition, should_blink
    """

    try:
        if airport in airport_conditions:
            return airport_conditions[airport][0], airport_conditions[airport][1]
    except:
        pass

    return weather.INVALID, True


def render_airport_displays(airport_flasher):
    """
    Sets the LEDs for all of the airports based on their flight rules.
    Does this independant of the LED type.

    Arguments:
        airport_flasher {bool} -- Is this on the "off" cycle of blinking.
    """

    try:
        thread_lock_object.acquire()

        for airport in airport_render_config:
            try:
                condition, blink = get_airport_condition(airport)
                color_to_render = color_by_rules[condition]
                if blink and airport_flasher:
                    color_to_render = colors[weather.OFF]

                renderer.set_led(
                    airport_render_config[airport], color_to_render)
            except:
                LOGGER.log_warning_message(
                    "Error attempting to render " + airport)
    finally:
        thread_lock_object.release()

#VFR - Green
#MVFR - Blue
#IFR - Red
# LIFR - Flashing red
# Error - Flashing white


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
    LOGGER.log_info_message("Starting rendering thread")

    while True:
        try:
            render_airport_displays(True)
            time.sleep(1)
            render_airport_displays(False)
        except KeyboardInterrupt:
            quit()
        finally:
            time.sleep(1)


def wait_for_all_airports():
    """
    Waits for all of the airports to have been given a chance to initialize.
    If an airport had an error, then that still counts.
    """

    airport_missing = True

    while airport_missing:
        airport_missing = False

        thread_lock_object.acquire()
        try:
            for airport in airport_render_config:
                if airport not in airport_conditions:
                    airport_missing = True
                    LOGGER.log_info_message("Waiting on " + airport)
                    break
        except:
            LOGGER.log_warning_message("Error while waiting for boot")
        finally:
            thread_lock_object.release()

        time.sleep(0.5)

    return True


if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    LOGGER.log_info_message("Initialize weather for all airports")

    weather.get_metars(airport_render_config.keys())

    # Test LEDS on startup
    colors_to_init = (
        weather.LOW,
        weather.RED,
        weather.BLUE,
        weather.GREEN,
        weather.YELLOW,
        weather.WHITE,
        weather.GRAY,
        weather.OFF
    )

    for color in colors_to_init:
        LOGGER.log_info_message("Setting to " + color)
        all_airports(color)
        time.sleep(2)

    all_airports(weather.YELLOW)

    update_weather_task = RecurringTask(
        'UpdateWeather', 10 * 60, LOGGER, True)
    update_categories_task = RecurringTask(
        'UpdateCategorizations', 60, update_all_station_categorizations, LOGGER, True)

    wait_for_all_airports()

    render_task = RecurringTask('Render', 0, render_thread, LOGGER, True)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt, SystemExit:
            break

    if not local_debug.is_debug():
        GPIO.cleanup()

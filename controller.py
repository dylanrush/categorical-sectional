# Live Sectional Map controller
# Dylan Rush 2017
# Additional modifications:
#   2018-2020, John Marzulli
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


import json
import logging
import logging.handlers
import re
import sys
import threading
import time
import urllib
from datetime import datetime

import lib.colors as colors_lib
import lib.local_debug as local_debug
import renderer
from configuration import configuration, configuration_server
from data_sources import weather
from lib import safe_logging
from lib.logger import Logger
from lib.recurring_task import RecurringTask

airport_conditions = {}
python_logger = logging.getLogger("weathermap")
python_logger.setLevel(logging.DEBUG)
LOGGER = Logger(python_logger)
HANDLER = logging.handlers.RotatingFileHandler(
    "weathermap.log",
    maxBytes=10485760,
    backupCount=10)
HANDLER.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
python_logger.addHandler(HANDLER)

thread_lock_object = threading.Lock()

if not local_debug.is_debug():
    import RPi.GPIO as GPIO
    try:
        GPIO.setmode(GPIO.BOARD)
    except:
        # ws281x causes an exception
        # when you try to set the board type
        pass

airport_render_config = configuration.get_airport_configs()
colors = configuration.get_colors()
color_by_rules = {
    weather.IFR: colors[weather.RED],
    weather.VFR: colors[weather.GREEN],
    weather.MVFR: colors[weather.BLUE],
    weather.LIFR: colors[weather.LOW],
    weather.NIGHT: colors[weather.YELLOW],
    weather.NIGHT_DARK: colors[weather.DARK_YELLOW],
    weather.SMOKE: colors[weather.GRAY],
    weather.INVALID: colors[weather.OFF],
    weather.INOP: colors[weather.OFF]
}

airport_render_last_logged_by_station = {}


renderer = renderer.get_renderer(airport_render_config)


def get_color_from_condition(
    category,
    metar=None
):
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [tuple] -- The color (also a tuple) and if it should blink.
    """

    is_old = False
    metar_age = None

    if metar is not None and metar != weather.INVALID:
        metar_age = weather.get_metar_age(metar)

    if metar_age is not None:
        metar_age_minutes = metar_age.total_seconds() / 60.0
        safe_logging.safe_log(
            LOGGER,
            "{} - Issued {:.1f} minutes ago".format(category, metar_age_minutes))

        is_old = metar_age_minutes > weather.DEFAULT_METAR_INVALIDATE_MINUTES
        is_inactive = metar_age_minutes > weather.DEFAULT_METAR_STATION_INACTIVE
    else:
        is_inactive = True

    # No report for a while?
    # Count the station as INOP.
    # The default is to follow what ForeFlight and SkyVector
    # do and just turn it off.
    if is_inactive:
        return (weather.INOP, False)

    should_blink = is_old and configuration.get_blink_station_if_old_data()

    if category == weather.VFR:
        return (weather.GREEN, should_blink)
    elif category == weather.MVFR:
        return (weather.BLUE, should_blink)
    elif category == weather.IFR:
        return (weather.RED, should_blink)
    elif category == weather.LIFR:
        # Only blink for normal LEDs.
        # PWM and WS2801 have their own color.
        return (weather.LOW, configuration.get_mode() == configuration.STANDARD)
    elif category == weather.NIGHT:
        return (weather.YELLOW, False)
    elif category == weather.SMOKE:
        return (weather.GRAY, should_blink)

    # Error
    return (weather.OFF, False)


def set_airport_display(
    airport,
    category,
    metar=None
):
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """
    safe_logging.safe_log(
        LOGGER, 'set_airport_display({}, {}, {})'.format(
            airport,
            category,
            metar))

    changed = False
    try:
        color_and_flash = get_color_from_condition(category, metar=metar)
        should_flash = color_and_flash[1]

        thread_lock_object.acquire()

        if airport in airport_conditions:
            changed = airport_conditions[airport][0] != category
        else:
            changed = True

        airport_conditions[airport] = (category, should_flash)
    except Exception as ex:
        safe_logging.safe_log_warning(
            LOGGER,
            'set_airport_display() - {} - EX:{}'.format(airport, ex))
    finally:
        thread_lock_object.release()

    if changed:
        safe_logging.safe_log(
            LOGGER,
            '{} NOW {}'.format(airport, category))

    safe_logging.safe_log(
        LOGGER,
        '~set_airport_display() => {}'.format(changed))

    return changed


def update_weather_for_all_stations():
    """
    Updates the weather for all of the stations.
    This does not update the conditions or category.
    """

    weather.get_metars(airport_render_config.keys(), logger=LOGGER)


def update_station_categorization(airport, utc_offset):
    """
    Updates the categorization for a single given station.

    Arguments:
        airport {string} -- The identifier of the weather station.
        utc_offset {int} -- The number of hours off from UTC the station is.
    """

    try:
        metar = weather.get_metar(airport, logger=LOGGER)
        category = get_airport_category(airport, metar, utc_offset)
        set_airport_display(airport, category, metar=metar)
    except Exception as e:
        safe_logging.safe_log_warning(
            LOGGER,
            'While attempting to get category for {}, got EX:{}'.format(airport, e))


def update_all_station_categorizations():
    """
    Takes the latest reports (probably in cache) and then
    updates the categorization of the airports.
    """

    utc_offset = datetime.utcnow() - datetime.now()

    safe_logging.safe_log(
        LOGGER,
        "update_all_station_categorizations(LOCAL={}, UTC={})".format(
            datetime.now(),
            datetime.utcnow()))

    [update_station_categorization(airport, utc_offset)
        for airport in airport_render_config]

    safe_logging.safe_log(
        LOGGER,
        '~update_all_station_categorizations()')


def get_airport_category(
    airport,
    metar,
    utc_offset
):
    """
    Gets the category of a single airport.

    Arguments:
        airport {string} -- The airport identifier.
        utc_offset {int} -- The offset from UTC to local for the airport.

    Returns:
        string -- The weather category for the airport.
    """
    category = weather.INVALID

    try:
        safe_logging.safe_log(
            LOGGER,
            'get_airport_category({}, {}, {})'.format(
                airport,
                metar,
                utc_offset))

        try:
            category = weather.get_category(airport, metar, logger=LOGGER)
            twilight = weather.get_civil_twilight(airport, logger=LOGGER)
            safe_logging.safe_log(
                LOGGER,
                "{} - Rise(UTC):{}, Set(UTC):{}".format(
                    airport,
                    twilight[1],
                    twilight[4]))
            safe_logging.safe_log(
                LOGGER, "{} - Rise(HERE):{}, Set(HERE):{}".format(
                    airport,
                    twilight[1] - utc_offset,
                    twilight[4] - utc_offset))
        except Exception as e:
            safe_logging.safe_log_warning(
                LOGGER,
                "Exception while attempting to categorize METAR:{} EX:{}".format(metar, e))
    except Exception as e:
        safe_logging.safe_log(
            LOGGER,
            "Captured EX while attempting to get category for {} EX:{}".format(airport, e))
        category = weather.INVALID

    safe_logging.safe_log(
        LOGGER,
        '~get_airport_category() => {}'.format(category))

    return category


def get_airport_condition(
    airport
):
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
    except Exception:
        pass

    return weather.INVALID, False


def render_airport_displays(
    airport_flasher
):
    """
    Sets the LEDs for all of the airports based on their flight rules.
    Does this independent of the LED type.

    Arguments:
        airport_flasher {bool} -- Is this on the "off" cycle of blinking.
    """

    for airport in airport_render_config:
        try:
            thread_lock_object.acquire()

            render_airport(airport, airport_flasher)
        except Exception as ex:
            safe_logging.safe_log_warning(
                LOGGER,
                'Catch-all error in render_airport_displays of {} EX={}'.format(airport, ex))
        finally:
            thread_lock_object.release()

    if renderer is not None:
        renderer.show()


def render_airport(
    airport,
    airport_flasher
):
    """
    Renders an airport.

    Arguments:
        airport {string} -- The identifier of the station.
        airport_flasher {bool} -- Is this a flash (off) cycle?
    """

    condition, blink = get_airport_condition(airport)
    color_by_category = color_by_rules[condition]

    now = datetime.utcnow()

    if blink and airport_flasher:
        color_by_category = colors[weather.OFF]

    proportions, color_to_render = get_mix_and_color(
        color_by_category,
        airport)

    log = airport not in airport_render_last_logged_by_station

    if airport in airport_render_last_logged_by_station:
        try:
            time_since_last = now - \
                airport_render_last_logged_by_station[airport]
            log = time_since_last.total_seconds() > 60
        except Exception as ex:
            safe_logging.safe_log(
                'Attempting to determine if should log, EX={}'.format(ex))
            log = True

    if log:
        message_format = 'STATION={}, CAT={:5}, BLINK={}, COLOR={:3}:{:3}:{:3}, P_O2N={:.1f}, P_N2C={:.1f}, RENDER={:3}:{:3}:{:3}'
        message = message_format.format(
            airport,
            condition,
            blink,
            color_by_category[0],
            color_by_category[1],
            color_by_category[2],
            proportions[0],
            proportions[1],
            color_to_render[0],
            color_to_render[1],
            color_to_render[2])
        safe_logging.safe_log(LOGGER, message)
        airport_render_last_logged_by_station[airport] = now

    if renderer is not None:
        renderer.set_led(
            airport_render_config[airport],
            color_to_render)


def _get_standard_led_night_color(
    starting_color,
    proportions
):
    """
    Returns the color to render for the chart for a STANDARD
    LED setup (+3 GPIO excitement, *_NOT_* addressable)

    Arguments:
        starting_color {array} -- The starting color descriptor
        proportions {tuple(float, float)} -- How far into the day/night transition.

    Returns:
        array -- The final color
    """

    if proportions[0] > 0.0 or proportions[1] < 1.0:
        return color_by_rules[weather.NIGHT]
    elif proportions[0] <= 0.0 and proportions[1] <= 0.0:
        return color_by_rules[weather.NIGHT_DARK]

    return starting_color


def __get_rgb_night_color_to_render__(
    color_by_category,
    proportions
):
    target_night_color = colors_lib.get_color_mix(
        colors[weather.OFF],
        color_by_category,
        configuration.get_night_category_proportion())

    # For the scenario where we simply dim the LED to account for sunrise/sunset
    # then only use the period between sunset/sunrise start and civil twilight
    if proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            color_by_category,
            target_night_color,
            proportions[0])
    elif proportions[1] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            target_night_color,
            color_by_category,
            proportions[1])
    else:
        color_to_render = target_night_color

    return color_to_render


def __get_night_color_to_render__(
    color_by_category: list,
    proportions: list
) -> list:
    """
    Calculate the color an airport should be based on the day/night cycle.
    Based on the configuration mixes the color with "Night Yellow" or dims the LEDs.
    A station that is in full daylight will be its normal color.
    A station that is in full darkness with be Night Yellow or dimmed to the night level.
    A station that is in sunset or sunrise will be mixed appropriately.

    Arguments:
        color_by_category {list} -- [description]
        proportions {list} -- [description]

    Returns:
        list -- [description]
    """

    color_to_render = weather.INOP

    if proportions[0] <= 0.0 and proportions[1] <= 0.0:
        if configuration.get_night_populated_yellow():
            color_to_render = colors[weather.DARK_YELLOW]
        else:
            color_to_render = __get_rgb_night_color_to_render__(
                color_by_category,
                proportions)
    # Do not allow color mixing for standard LEDs
    # Instead if we are going to render NIGHT then
    # have the NIGHT color represent that the station
    # is in a twilight period.
    elif configuration.get_mode() == configuration.STANDARD:
        if proportions[0] > 0.0 or proportions[1] < 1.0:
            color_to_render = color_by_rules[weather.NIGHT]
        elif proportions[0] <= 0.0 and proportions[1] <= 0.0:
            color_to_render = colors[weather.DARK_YELLOW]
    elif not configuration.get_night_populated_yellow():
        color_to_render = __get_rgb_night_color_to_render__(
            color_by_category,
            proportions)
    elif proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            colors[weather.DARK_YELLOW],
            color_by_rules[weather.NIGHT],
            proportions[0])
    elif proportions[1] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            color_by_rules[weather.NIGHT],
            color_by_category,
            proportions[1])

    return color_to_render


def __get_dimmed_color__(
    starting_color: list
) -> list:
    """
    Given a starting color, get the version that is dimmed.

    Arguments:
        starting_color {list} -- The starting color that will be dimmed.

    Returns:
        list -- The color with the dimming adjustment.
    """
    dimmed_color = []
    brightness_adjustment = configuration.get_brightness_proportion()
    for color in starting_color:
        reduced_color = float(color) * brightness_adjustment

        # Some colors are floats, some are integers.
        # Make sure we keep everything the same.
        if isinstance(color, int):
            reduced_color = int(reduced_color)

        dimmed_color.append(reduced_color)

    return dimmed_color


def get_mix_and_color(
    color_by_category,
    airport
):
    """
    Gets the proportion of color mixes (dark to NIGHT, NIGHT to color) and the final color to render.

    Arguments:
        color_by_category {tuple} -- the initial color decided upon by weather.
        airport {string} -- The station identifier.

    Returns:
        tuple -- proportion, color to render
    """

    color_to_render = color_by_category
    proportions = weather.get_twilight_transition(airport)

    if configuration.get_night_lights():
        color_to_render = __get_night_color_to_render__(
            color_by_category,
            proportions)

    final_color = []
    brightness_adjustment = configuration.get_brightness_proportion()
    for color in color_to_render:
        reduced_color = float(color) * brightness_adjustment

        # Some colors are floats, some are integers.
        # Make sure we keep everything the same.
        if isinstance(color, int):
            reduced_color = int(reduced_color)

        final_color.append(reduced_color)

    return proportions, final_color

# VFR - Green
# MVFR - Blue
# IFR - Red
# LIFR - Flashing red
# Error - Flashing white


def all_airports(
    color
):
    """
    Sets all of the airports to the given color

    Arguments:
        color {triple} -- Three integer tuple(triple?) of the RGB values
        of the color to set for ALL airports.
    """

    if renderer is None:
        return

    [renderer.set_led(airport_render_config[airport], colors[color])
        for airport in airport_render_config]

    renderer.show()


def __all_leds_to_color__(
    color: list
):
    if renderer is None:
        return
    
    renderer.set_all(color)

def render_thread():
    """
    Main logic loop for rendering the lights.
    """

    safe_logging.safe_log(
        LOGGER,
        "Starting rendering thread")

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

    utc_offset = datetime.utcnow() - datetime.now()

    for airport in airport_render_config:
        try:
            thread_lock_object.acquire()
            metar = weather.get_metar(airport, logger=LOGGER)
            category = get_airport_category(airport, metar, utc_offset)
            airport_conditions[airport] = (category, False)
        except Exception:
            airport_conditions[airport] = (weather.INVALID, False)
            safe_logging.safe_log_warning(
                LOGGER,
                "Error while initializing with airport={}".format(airport))
        finally:
            thread_lock_object.release()

    return True


def __get_test_cycle_colors__() -> list:
    base_colors_test = [
        weather.LOW,
        weather.RED,
        weather.BLUE,
        weather.GREEN,
        weather.YELLOW,
        weather.WHITE,
        weather.GRAY,
        weather.DARK_YELLOW
    ]

    colors_to_init = []

    for color in base_colors_test:
        is_global_dimming = configuration.get_brightness_proportion() < 1.0
        color_to_cycle = colors[color]
        colors_to_init.append(color_to_cycle)
        if is_global_dimming:
            colors_to_init.append(__get_dimmed_color__(color_to_cycle))
        colors_to_init.append(__get_night_color_to_render__(
            color_to_cycle,
            [0.0, 0.0]))
        if is_global_dimming:
            colors_to_init.append(__get_dimmed_color__(
                __get_night_color_to_render__(
                    color_to_cycle,
                    [0.0, 0.0])))

    colors_to_init.append(colors[weather.OFF])

    return colors_to_init


def __test_all_leds__(
    logger: Logger
):
    """
    Test all of the LEDs, independent of the configuration
    to make sure the wiring is correct and that none have failed.

    Arguments:
        logger {Logger} -- The logger being used.
    """
    for color in __get_test_cycle_colors__():
        safe_logging.safe_log(
            logger,
            "Setting to {}".format(color))
        __all_leds_to_color__(color)
        time.sleep(0.5)


if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    safe_logging.safe_log(
        LOGGER,
        "Initialize weather for all airports")

    weather.get_metars(airport_render_config.keys(), logger=LOGGER)

    __test_all_leds__(LOGGER)

    web_server = configuration_server.WeatherMapServer()

    all_airports(weather.OFF)

    RecurringTask(
        'UpdateCategorizations',
        60,
        update_all_station_categorizations,
        LOGGER,
        True)

    RecurringTask(
        "rest_host",
        0.1,
        web_server.run,
        LOGGER,
        True)

    wait_for_all_airports()

    render_task = RecurringTask('Render', 0, render_thread, LOGGER, True)

    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break

    if not local_debug.is_debug():
        GPIO.cleanup()

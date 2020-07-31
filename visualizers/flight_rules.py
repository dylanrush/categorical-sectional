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
from configuration import configuration
from data_sources import weather
from lib import safe_logging
from lib.logger import Logger
from lib.recurring_task import RecurringTask

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

airport_render_config = configuration.get_airport_configs()


def render_airport_displays(
    renderer,
    logger: Logger,
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
            render_airport(renderer, logger, airport, airport_flasher)
        except Exception as ex:
            safe_logging.safe_log_warning(
                logger,
                'Catch-all error in render_airport_displays of {} EX={}'.format(airport, ex))

    renderer.show()


def get_airport_category(
    logger: Logger,
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
        try:
            category = weather.get_category(airport, metar, logger=logger)
            twilight = weather.get_civil_twilight(airport, logger=logger)
        except Exception as e:
            safe_logging.safe_log_warning(
                logger,
                "Exception while attempting to categorize METAR:{} EX:{}".format(metar, e))
    except Exception as e:
        safe_logging.safe_log(
            logger,
            "Captured EX while attempting to get category for {} EX:{}".format(airport, e))
        category = weather.INVALID

    return category


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
        return (weather.LOW, should_blink)
    elif category == weather.NIGHT:
        return (weather.YELLOW, False)
    elif category == weather.SMOKE:
        return (weather.GRAY, should_blink)

    # Error
    return (weather.OFF, False)


def get_airport_condition(
    logger: Logger,
    airport: str
):
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """

    try:
        utc_offset = datetime.utcnow() - datetime.now()
        metar = weather.get_metar(airport)
        category = get_airport_category(logger, airport, metar, utc_offset)
        color, should_flash = get_color_from_condition(category, metar)

        return category, should_flash
    except Exception as ex:
        safe_logging.safe_log_warning(
            logger,
            'set_airport_display() - {} - EX:{}'.format(airport, ex))

        return weather.INOP, True


def render_airport(
    renderer,
    logger: Logger,
    airport,
    airport_flasher
):
    """
    Renders an airport.

    Arguments:
        airport {string} -- The identifier of the station.
        airport_flasher {bool} -- Is this a flash (off) cycle?
    """

    condition, blink = get_airport_condition(logger, airport)
    color_by_category = color_by_rules[condition]

    now = datetime.utcnow()

    if blink and airport_flasher:
        color_by_category = colors[weather.OFF]

    proportions, color_to_render = get_mix_and_color(
        color_by_category,
        airport)

    renderer.set_led(
        airport_render_config[airport],
        color_to_render)


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


class FlightRulesVisualizer(object):
    def __init__(
        self,
        logger: Logger
    ):
        super().__init__()

        self.__logger__ = logger

    def update(
        self,
        renderer,
        time_slice: float
    ):
        render_airport_displays(
                renderer,
                self.__logger__,
                True)

        time.sleep(1.0)

        render_airport_displays(
                renderer,
                self.__logger__,
                False)

        time.sleep(1.0)

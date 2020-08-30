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
from lib import safe_logging, colors
from lib.logger import Logger
from lib.recurring_task import RecurringTask
from visualizers.visualizer import Visualizer

rgb_colors = colors.get_colors()
color_by_rules = {
    weather.IFR: rgb_colors[colors.RED],
    weather.VFR: rgb_colors[colors.GREEN],
    weather.MVFR: rgb_colors[colors.BLUE],
    weather.LIFR: rgb_colors[colors.MAGENTA],
    weather.NIGHT: rgb_colors[colors.YELLOW],
    weather.NIGHT_DARK: rgb_colors[colors.DARK_YELLOW],
    weather.SMOKE: rgb_colors[colors.GRAY],
    weather.INVALID: rgb_colors[colors.OFF],
    weather.INOP: rgb_colors[colors.OFF]
}

airport_render_config = configuration.get_airport_configs()


def render_airport_displays(
    renderer,
    logger: Logger,
    airport_flasher
) -> float:
    """
    Sets the LEDs for all of the airports based on their flight rules.
    Does this independent of the LED type.

    Arguments:
        airport_flasher {bool} -- Is this on the "off" cycle of blinking.
    """

    start_time = datetime.utcnow()

    for airport in airport_render_config:
        try:
            render_airport(renderer, logger, airport, airport_flasher)
        except Exception as ex:
            safe_logging.safe_log_warning(
                logger,
                'Catch-all error in render_airport_displays of {} EX={}'.format(airport, ex))

    renderer.show()

    runtime = datetime.utcnow() - start_time

    return runtime.total_seconds()


def get_airport_category(
    logger: Logger,
    airport: str,
    metar: str
) -> str:
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
            # logger.log_info_message("Getting category for {}".format(airport))
            category = weather.get_category(airport, metar, logger=logger)
            # logger.log_info_message("{}={}".format(airport, category))
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
    category: str
) -> str:
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [str] -- The color name that should be displayed.
    """

    if category == weather.VFR:
        return colors.GREEN
    elif category == weather.MVFR:
        return colors.BLUE
    elif category == weather.IFR:
        return colors.RED
    elif category == weather.LIFR:
        return colors.MAGENTA
    elif category == weather.NIGHT:
        return colors.YELLOW
    elif category == weather.SMOKE:
        return colors.GRAY

    # Error
    return colors.OFF


def should_station_flash(
    metar: str
) -> bool:
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
        return False

    should_blink = is_old and configuration.get_blink_station_if_old_data()

    return should_blink


def get_airport_condition(
    logger: Logger,
    airport: str
) -> str:
    """
    Sets the given airport to have the given flight rules category.

    Arguments:
        airport {str} -- The airport identifier.
        category {string} -- The flight rules category.

    Returns:
        bool -- True if the flight category changed (or was set for the first time).
    """

    try:
        metar = weather.get_metar(airport)
        # logger.log_info_message("{}={}".format(airport, metar))
        category = get_airport_category(logger, airport, metar)
        # logger.log_info_message("{}={}".format(airport, category))
        should_flash = should_station_flash(metar)

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
    color_name_by_category = get_color_from_condition(condition)
    color_by_category = rgb_colors[color_name_by_category]

    if airport_flasher:
        metar = weather.get_metar(airport, logger)
        is_lightning = weather.is_lightning(metar)

        if is_lightning:
            color_by_category = rgb_colors[colors.YELLOW]

    if blink and airport_flasher:
        color_by_category = rgb_colors[colors.OFF]

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
        rgb_colors[colors.OFF],
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
            color_to_render = rgb_colors[colors.DARK_YELLOW]
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
            color_to_render = rgb_colors[colors.DARK_YELLOW]
    elif not configuration.get_night_populated_yellow():
        color_to_render = __get_rgb_night_color_to_render__(
            color_by_category,
            proportions)
    elif proportions[0] > 0.0:
        color_to_render = colors_lib.get_color_mix(
            rgb_colors[colors.DARK_YELLOW],
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

    brightness_adjustment = configuration.get_brightness_proportion()
    final_color = colors_lib.get_brightness_adjusted_color(
        color_to_render,
        brightness_adjustment)

    return proportions, final_color

# VFR - Green
# MVFR - Blue
# IFR - Red
# LIFR - Flashing red
# Error - Flashing white


class FlightRulesVisualizer(Visualizer):
    def __init__(
        self,
        logger: Logger
    ):
        super().__init__(logger)

        self.__logger__ = logger

    def update(
        self,
        renderer,
        time_slice: float
    ):
        for blink in [True, False]:
            seconds_run = render_airport_displays(
                renderer,
                self.__logger__,
                blink)

            time_to_sleep = 1.0 - seconds_run

            if time_to_sleep > 0.0:
                time.sleep(time_to_sleep)

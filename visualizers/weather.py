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
from lib import colors as colors_lib
from lib import safe_logging
from lib.logger import Logger
from lib.recurring_task import RecurringTask
from visualizers.flight_rules import get_mix_and_color
from visualizers.visualizer import Visualizer

airport_render_config = configuration.get_airport_configs()


def celsius_to_fahrenheit(
    temperature_celsius: float
):
    if temperature_celsius is None:
        return 0

    return (temperature_celsius * (9.0 / 5.0)) + 32.0


def get_proportion_between_temperatures(
    start: float,
    current: float,
    end: float
):
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current is.
    IE:
        If the Current is the same as Start, then the result will be 0.0
        If the Current is the same as the End, then the result will be 1.0
        If the Current is halfway between Start and End, then the result will be 0.5


    Arguments:
        start {float} -- The starting temp.
        current {float} -- The temp we want to get the proportion for.
        end {float} -- The end temp to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End
    """

    total_delta = (end - start)
    time_in = (current - start)

    return time_in / total_delta


def get_color_by_temperature_celsius(
    temperature_celsius: float
):
    colors_by_name = colors_lib.get_colors()

    if temperature_celsius is None:
        return colors_by_name[colors_lib.OFF]

    temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)

    if temperature_fahrenheit < 0:
        return colors_by_name[colors_lib.PURPLE]

    if temperature_fahrenheit < 20:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.PURPLE],
            colors_by_name[colors_lib.BLUE],
            get_proportion_between_temperatures(
                0,
                temperature_fahrenheit,
                20))

    if temperature_fahrenheit < 40:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.BLUE],
            colors_by_name[colors_lib.GREEN],
            get_proportion_between_temperatures(
                20,
                temperature_fahrenheit,
                40))

    if temperature_fahrenheit < 60:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.GREEN],
            colors_by_name[colors_lib.YELLOW],
            get_proportion_between_temperatures(
                40,
                temperature_fahrenheit,
                60))

    if temperature_fahrenheit < 80:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.YELLOW],
            colors_by_name[colors_lib.ORANGE],
            get_proportion_between_temperatures(
                60,
                temperature_fahrenheit,
                80))

    if temperature_fahrenheit < 100:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.ORANGE],
            colors_by_name[colors_lib.RED],
            get_proportion_between_temperatures(
                80,
                temperature_fahrenheit,
                100))

    return colors_by_name[colors_lib.RED]


def render_airport(
    renderer,
    logger: Logger,
    airport
):
    """
    Renders an airport.

    Arguments:
        airport {string} -- The identifier of the station.
    """

    metar = weather.get_metar(airport, logger)
    temperature = weather.get_temperature(metar)
    color_to_render = get_color_by_temperature_celsius(temperature)
    proportions, color_to_render = get_mix_and_color(color_to_render, airport)
    brightness_adjustment = configuration.get_brightness_proportion()
    final_color = colors_lib.get_brightness_adjusted_color(
        color_to_render,
        brightness_adjustment)

    renderer.set_led(
        airport_render_config[airport],
        final_color)


def render_airport_displays(
    renderer,
    logger: Logger
):
    """
    Sets the LEDs for all of the airports based on their flight rules.
    Does this independent of the LED type.

    Arguments:
        airport_flasher {bool} -- Is this on the "off" cycle of blinking.
    """

    for airport in airport_render_config:
        try:
            render_airport(renderer, logger, airport)
        except Exception as ex:
            safe_logging.safe_log_warning(
                logger,
                'Catch-all error in render_airport_displays of {} EX={}'.format(airport, ex))

    renderer.show()


class TemperatureVisualizer(Visualizer):
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
        render_airport_displays(
            renderer,
            self.__logger__)

        time.sleep(1.0)

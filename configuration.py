"""
Handles configuration loading and constants.
"""
import json
import os
import unicodedata

import lib.local_debug as local_debug
import weather

if local_debug.is_debug():
    HIGH = 1
    LOW = 0
else:
    import RPi.GPIO as GPIO
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW

CONFIG_FILE = "./data/config.json"
__working_dir__ = os.path.dirname(os.path.abspath(__file__))
__full_config__ = os.path.join(__working_dir__, os.path.normpath(CONFIG_FILE))

# Modes
STANDARD = 'led'
PWM = 'pwm'
WS2801 = 'ws2801'


with open(__full_config__) as config_file:
    config_text = config_file.read()
    CONFIG = json.loads(config_text)


def get_mode():
    """
    Returns the mode given in the config.
    """

    return CONFIG['mode']


def get_night_lights():
    """
    Should we light airports that are in Night differently?

    Returns:
        boolean -- True if we should light airports that are in the dark
        differently.
    """

    try:
        if CONFIG is not None and 'night_lights' in CONFIG:
            return CONFIG['night_lights']
    except:
        return False

def get_night_populated_yellow():
    """
    If we are using the option feature that shows day/night cycles,
    then should we use "populated yellow" as the target color?
    Defaults to True if the option is not in the config file.

    Returns:
        boolean -- True if the color of the station should be yellow when it is dark.
    """
    try:
        if CONFIG is not None and 'night_populated_yellow' in CONFIG:
            return CONFIG['night_populated_yellow']
    except:
        return True

def get_night_category_proportion():
    """
    If we are using the category color for the night conditions,
    then what proportion between the category and black should we use?
    0.0 is black. 1.0 is the normal category color.

    Returns:
        float -- A number between 0.0 (off) and 1.0 (true category color), inclusive
    """
    try:
        if CONFIG is not None and 'night_category_proportion' in CONFIG:
            try:
                unclamped =  float(CONFIG['night_category_proportion'])

                if unclamped < 0.0:
                    return 0.0
                
                if unclamped > 1.0:
                    return 1.0

                return unclamped
            except:
                return 0.5
    except:
        return 0.5

def get_airport_configuration_section():
    """
    Returns the proper section of the configuration file
    to load the airport configuration from.

    Returns:
        string -- The key in the configuration JSON to
        load the airport configuration from.
    """

    mode = get_mode()

    if mode == STANDARD:
        return PWM

    return mode


def get_airport_file():
    """
    Returns the file that contains the airport config
    """

    full_config = os.path.join(
        __working_dir__, os.path.normpath(CONFIG['airports_file']))

    return full_config


def get_colors():
    """
    Returns the colors based on the config.
    """

    if get_mode() == WS2801:
        return __get_ws2801_colors__()
    elif get_mode() == PWM:
        return __get_pwm_colors__()

    return __get_led_colors__()


def __get_led_colors__():
    """
    Returns colors for normal GPIO use.
    """
    return {
        weather.RED: (HIGH, LOW, LOW),
        weather.GREEN: (LOW, HIGH, LOW),
        weather.BLUE: (LOW, LOW, HIGH),
        weather.LOW: (HIGH, LOW, LOW),
        weather.OFF: (LOW, LOW, LOW),
        weather.YELLOW: (HIGH, HIGH, LOW),
        weather.GRAY: (LOW, LOW, LOW),
        weather.WHITE: (HIGH, HIGH, HIGH)
    }


def __get_pwm_colors__():
    """Returns colors for Pulse Width Modulation control

    Returns:
        dictionary -- Color keys to frequency
    """

    return {
        weather.RED: (20.0, 0.0, 0.0),
        weather.GREEN: (0.0, 50.0, 0.0),
        weather.BLUE: (0.0, 0.0, 100.0),
        weather.LOW: (20.0, 0.0, 100.0),
        weather.OFF: (0.0, 0.0, 0.0),
        weather.GRAY: (10.0, 20.0, 40.0),
        weather.YELLOW: (20.0, 50.0, 0.0),
        weather.WHITE: (20.0, 50, 100.0)
    }


def __get_ws2801_colors__():
    """
    Returns the color codes for a WS2801 based light set.
    """

    return {
        weather.RED: (255, 0, 0),
        weather.GREEN: (0, 255, 0),
        weather.BLUE: (0, 0, 255),
        weather.LOW: (255, 0, 255),
        weather.OFF: (0, 0, 0),
        weather.GRAY: (50, 50, 50),
        weather.YELLOW: (255, 255, 0),
        weather.DARK_YELLOW: (20, 20, 0),
        weather.WHITE: (255, 255, 255)
    }


def get_airport_configs():
    """
    Returns the configuration for the lighting type

    Returns:
        dictionary -- Airport identitifier keying lighting configuration.
    """

    mode = CONFIG['mode']
    if mode == PWM or mode == STANDARD:
        return __load_gpio_airport_pins__(get_airport_file())
    elif mode == WS2801:
        return __load_airport_ws2801__(get_airport_file())
    else:
        raise 'Unable to determine light types'


def __load_gpio_airport_pins__(config_file):
    """
    Loads the mapping of airport IACO codes to the GPIO
    pin mapping from the configuration file.

    Returns:
        Map -- A dictionary of GPIO pin tuples keyed by IACO code.
    """

    out_airport_pins_map = {}
    with open(config_file, encoding='UTF8') as gpio_config_file:
        json_config_text = gpio_config_file.read()
        json_config = json.loads(json_config_text)
        airports = json_config[get_airport_configuration_section()]

        for airport_data in airports:
            airport_code = airport_data.keys()[0]
            out_airport_pins_map[airport_code.upper()] = (airport_data[airport_code][0],
                                                          airport_data[airport_code][1],
                                                          airport_data[airport_code][2])

        return out_airport_pins_map


def __load_airport_ws2801__(config_file):
    """
    Loads the configuration for WS2801/neopixel based setups.

    Arguments:
        config_file {string} -- The file name & location to load.

    Returns:
        dictionary -- A dictionary keyed by airport identitifier
                      that holds the pixel index and a reserved value.
    """

    out_airport_map = {}
    with open(config_file, encoding='UTF8') as ws2801_config_file:
        json_config_text = ws2801_config_file.read()
        json_config = json.loads(json_config_text)
        airports = json_config[WS2801]

        for airport_data in airports:
            keylist = []
            keylist.extend(iter(airport_data.keys()))
            airport_code = keylist[0]

            out_airport_map[airport_code.upper(
            )] = airport_data[airport_code]['neopixel']

        return out_airport_map

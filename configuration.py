import json
import weather
import unicodedata
import lib.local_debug as local_debug

if local_debug.is_debug():
    HIGH = 1
    LOW = 0
else:
    import RPi.GPIO as GPIO
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW

CONFIG_FILE = "./data/config.json"

# Modes
STANDARD = 'led'
PWM = 'pwm'
WS2801 = 'ws2801'


with open(CONFIG_FILE) as config_file:
    config_text = config_file.read()
    CONFIG = json.loads(config_text)


def get_mode():
    """
    Returns the mode given in the config.
    """

    return CONFIG['mode']


def get_render_mode():
    mode = get_mode()

    if mode == STANDARD:
        return PWM

    return mode


def get_airport_file():
    """
    Returns the file that contains the airport config
    """

    return CONFIG['airports_file']


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
        weather.LOW: (LOW, LOW, LOW),
        weather.OFF: (LOW, LOW, LOW)
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
        weather.OFF: (0.0, 0.0, 0.0)
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
        weather.OFF: (0, 0, 0)
    }


def get_overrides():
    # {'KOLM': 'VFR',
    #  'KTIW': 'MVFR',
    #  'KPWT': 'INVALID'}
    return {}


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
    with open(config_file) as gpio_config_file:
        json_config_text = gpio_config_file.read()
        json_config = json.loads(json_config_text)
        airports = json_config[get_render_mode()]

        for airport_data in airports:
            airport_code = airport_data.keys()[0]
            out_airport_pins_map[airport_code.upper()] = (airport_data[airport_code][0],
                                                          airport_data[airport_code][1],
                                                          airport_data[airport_code][2])

        return out_airport_pins_map


def __load_airport_ws2801__(config_file):
    out_airport_map = {}
    with open(config_file) as ws2801_config_file:
        json_config_text = ws2801_config_file.read()
        json_config = json.loads(json_config_text)
        airports = json_config[WS2801]

        for airport_data in airports:
            airport_code = airport_data.keys()[0]
            out_airport_map[airport_code.upper()] = (
                airport_data[airport_code]['neopixel'], airport_data[airport_code]['utc_offset'])

        return out_airport_map

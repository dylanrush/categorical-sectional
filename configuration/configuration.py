"""
Handles configuration loading and constants.
"""
import json
import os
import threading
import unicodedata
from pathlib import Path

from data_sources import weather
from lib import local_debug

if local_debug.is_debug():
    HIGH = 1
    LOW = 0
else:
    import RPi.GPIO as GPIO
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW

# Modes
STANDARD = 'led'
PWM = 'pwm'
WS2801 = 'ws2801'

LED_MODE_KEY = "mode"
PIXEL_COUNT_KEY = "pixel_count"
SPI_DEVICE_KEY = "spi_device"
SPI_PORT_KEY = "spi_port"
PWM_FREQUENCY_KEY = "pwm_frequency"
AIRPORTS_FILE_KEY = "airports_file"
BLINK_OLD_STATIONS_KEY = "blink_old_stations"
NIGHT_LIGHTS_KEY = "night_lights"
NIGHT_POPULATED_YELLOW_KEY = "night_populated_yellow"
NIGHT_CATEGORY_PROPORTION_KEY = "night_category_proportion"
BRIGHTNESS_PROPORTION_KEY = "brightness_proportion"

__VALID_KEYS__ = [
    LED_MODE_KEY,
    PIXEL_COUNT_KEY,
    SPI_DEVICE_KEY,
    SPI_PORT_KEY,
    PWM_FREQUENCY_KEY,
    AIRPORTS_FILE_KEY,
    BLINK_OLD_STATIONS_KEY,
    NIGHT_LIGHTS_KEY,
    NIGHT_POPULATED_YELLOW_KEY,
    NIGHT_CATEGORY_PROPORTION_KEY,
    BRIGHTNESS_PROPORTION_KEY
]

__DEFAULT_CONFIG_FILE__ = '../data/config.json'
__USER_CONFIG_FILE__ = '~/weather_map/config.json'

__lock__ = threading.Lock()


def __get_resolved_filepath__(
    filename: str
) -> str:
    """
    Try to resolve a filename to the proper full path.
    Used to help resolve relative path issues and issues with the working path when started from crontab.

    Arguments:
        filename {str} -- The filename (optionally with a partial path) to resolve to a fully qualified file path.

    Returns:
        str -- The fully resolved filepath
    """

    print("Attempting to resolve '{}'".format(filename))
    print("__file__='{}'".format(__file__))

    try:
        raw_path = filename

        if './' in filename:
            raw_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                filename)
        else:
            raw_path = str(Path(os.path.expanduser(filename)).resolve())

        print("Before normalization path='{}'".format(raw_path))

        normalized_path = os.path.normpath(raw_path)

        print("Normalized path='{}'".format(raw_path))

        return normalized_path
    except:
        return None


def __load_config_file__(
    config_filename: str
) -> dict:
    """
    Loads a configuration file from the given source.

    Arguments:
        config_filename {str} -- The path to the configuration file to load.

    Returns:
        dict -- Any given configuration found.
    """
    try:
        full_filename = __get_resolved_filepath__(config_filename)

        with open(str(full_filename)) as config_file:
            config_text = config_file.read()
            configuration = json.loads(config_text)

            return configuration
    except Exception as ex:
        print("Error while trying to load {}: EX={}".format(config_filename, ex))
        return {}


def __get_configuration__() -> dict:
    """
    Loads the default configuration. Then loads any user configuration and applies the new data over the defaults.

    Returns:
        dict -- The default configuration with the user changes applied over top.
    """
    configuration = __load_config_file__(__DEFAULT_CONFIG_FILE__)
    user_configuration = __load_config_file__(__USER_CONFIG_FILE__)

    configuration.update(user_configuration)

    return configuration


CONFIG = __get_configuration__()


def __write_user_configuration__(
    config: dict
) -> bool:
    """
    Writes the current configuration to the user directory.

    Returns:
        bool -- True if the configuration was written to disk
    """
    try:
        print("Starting to write file.")

        full_filename = None

        try:
            full_filename = __get_resolved_filepath__(__USER_CONFIG_FILE__)
            print("full_filename=`{}`".format(full_filename))
        except:
            pass

        if full_filename is None:
            print("Unable to resolve, using relative path + name instead.")
            full_filename = __USER_CONFIG_FILE__

        directory = os.path.dirname(full_filename)
        print("directory=`{}`".format(directory))

        if not os.path.exists(directory):
            print("Attempting to create directory `{}`".format(directory))
            os.mkdir(directory)

        with open(str(full_filename), "w") as config_file:
            print("Opened `{}` for write.".format(full_filename))

            config_text = json.dumps(config, indent=4, sort_keys=True)
            print("config_text=`{}`".format(config_text))

            config_file.write(config_text)

            print("Finished writing file.")

            return True
    except Exception as ex:
        print(
            "Error while trying to write {}: EX={}".format(
                __USER_CONFIG_FILE__,
                ex))
        return False


def update_configuration(
    new_config: dict
) -> dict:
    """
    Given a new piece of configuration, update it gracefully.

    Arguments:
        new_config {dict} -- The new configuration... partial or whole.

    Returns:
        dict -- The updated configuration.
    """
    if new_config is None:
        return CONFIG.copy()

    update_package = {}

    for valid_key in __VALID_KEYS__:
        if valid_key in new_config:
            update_package[valid_key] = new_config[valid_key]

    __lock__.acquire()
    CONFIG.update(update_package)
    config_copy = CONFIG.copy()
    __lock__.release()

    __write_user_configuration__(config_copy)

    return config_copy


def __get_boolean_config_value__(
    config_key: str,
    default: bool = False
) -> bool:
    """
    Get a configuration value from the config that is a boolean.
    If the value is not in the config, then use the default.

    Arguments:
        config_key {str} -- The name of the setting.
        default {bool} -- The default value if the setting is not found.

    Returns:
        bool -- The value to use for the configuration.
    """
    try:
        if CONFIG is not None and config_key in CONFIG:
            return CONFIG[config_key]
    except:
        return default


def get_mode():
    """
    Returns the mode given in the config.
    """

    return CONFIG['mode']


def get_blink_station_if_old_data() -> bool:
    """
    Should old stations blink if the data is considered too old?

    Returns:
        bool -- Should the station be blinked if the data is too old?
    """

    return __get_boolean_config_value__('blink_old_stations', True)


def get_night_lights():
    """
    Should we light airports that are in Night differently?

    Returns:
        boolean -- True if we should light airports that are in the dark
        differently.
    """
    return __get_boolean_config_value__('night_lights')


def get_night_populated_yellow():
    """
    If we are using the option feature that shows day/night cycles,
    then should we use "populated yellow" as the target color?
    Defaults to True if the option is not in the config file.

    Returns:
        boolean -- True if the color of the station should be yellow when it is dark.
    """
    return __get_boolean_config_value__('night_populated_yellow', True)


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
                unclamped = float(CONFIG['night_category_proportion'])

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


def get_brightness_proportion() -> float:
    """
    Get how much we want to adjust the brightness of the LEDs

    Returns:
        float -- The amount that the final color will be multiplied by
    """
    try:
        if CONFIG is not None and 'brightness_proportion' in CONFIG:
            return CONFIG['brightness_proportion']
    except:
        return 1.0


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
        dictionary -- Airport identifier keying lighting configuration.
    """

    mode = CONFIG['mode']
    if mode == PWM or mode == STANDARD:
        return __load_gpio_airport_pins__(get_airport_file())
    elif mode == WS2801:
        return __load_airport_ws2801__(get_airport_file())
    else:
        raise Exception('Unable to determine light types')


def __load_gpio_airport_pins__(
    config_file: str
) -> dict:
    """
    Loads the mapping of airport ICAO codes to the GPIO
    pin mapping from the configuration file.

    Returns:
        dict -- A dictionary of GPIO pin tuples keyed by ICAO code.
    """

    out_airport_pins_map = {}

    json_config = __load_config_file__(config_file)

    airports = json_config[get_airport_configuration_section()]

    for airport_data in airports:
        airport_code = airport_data.keys()[0]
        out_airport_pins_map[airport_code.upper()] = (
            airport_data[airport_code][0],
            airport_data[airport_code][1],
            airport_data[airport_code][2])

    return out_airport_pins_map


def __load_airport_ws2801__(
    config_file: str
) -> dict:
    """
    Loads the configuration for WS2801/neopixel based setups.

    Arguments:
        config_file {string} -- The file name & location to load.

    Returns:
        dict -- A dictionary keyed by airport identifier that holds the pixel index and a reserved value.
    """

    out_airport_map = {}

    json_config = __load_config_file__(config_file)
    airports = json_config[WS2801]

    for airport_data in airports:
        keylist = []
        keylist.extend(iter(airport_data.keys()))
        airport_code = keylist[0]
        normalized_code = airport_code.upper()

        out_airport_map[normalized_code] = airport_data[airport_code]['neopixel']

    return out_airport_map

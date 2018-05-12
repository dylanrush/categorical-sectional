import json
import weather
import lib.local_debug as local_debug

if local_debug.is_debug():
    HIGH = 1
    LOW = 0
else:
    import RPi.GPIO as GPIO
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW

# Modes
STANDARD = 'STANDARD'
PWM = 'PWM'

MODE = PWM

def get_colors():
    """
    Returns colors for normal GPIO use.
    """
    return {
        weather.RED: (HIGH, LOW, LOW),
        weather.GREEN: (LOW, HIGH, LOW),
        weather.BLUE: (LOW, LOW, HIGH),
        weather.LOW: (LOW, LOW, LOW)
    }


def get_pwm_colors():
    """Returns colors for Pulse Width Modulation control

    Returns:
        dictionary -- Color keys to frequency
    """

    return {
        weather.RED: (20.0, 0.0, 0.0),
        weather.GREEN: (0.0, 50.0, 0.0),
        weather.BLUE: (0.0, 0.0, 100.0),
        weather.LOW: (0.0, 0.0, 0.0)
    }


def get_overrides():
    # {'KOLM': 'VFR',
    #  'KTIW': 'MVFR',
    #  'KPWT': 'INVALID'}
    return {}


def load_gpio_airport_pins(config_file):
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
        airports = json_config['airports']

        for airport_data in airports:
            airport_code = airport_data.keys()[0]
            out_airport_pins_map[airport_code.upper()] = (airport_data[airport_code][0],
                                                          airport_data[airport_code][1],
                                                          airport_data[airport_code][2])

        return out_airport_pins_map

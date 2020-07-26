# Self-Test file that makes sure all
# off the wired lights are functional.

import logging
import time

import lib.local_debug as local_debug
from configuration import configuration
from data_sources import weather
from lib import safe_logging
from lib.logger import Logger
from renderers import led, led_pwm, ws2801, ws281x

python_logger = logging.getLogger("check_lights_wiring")
python_logger.setLevel(logging.DEBUG)
LOGGER = Logger(python_logger)

if not local_debug.IS_PI:
    safe_logging.safe_log_warning(
        LOGGER,
        "This is only able to run on a Raspberry Pi.")

    exit(0)

airport_render_config = configuration.get_airport_configs()
colors = configuration.get_colors()


def get_test_renderer():
    """
    Returns the renderer to use based on the type of
    LED lights given in the config.

    Returns:
        renderer -- Object that takes the colors and airport config and
        sets the LEDs.
    """

    if configuration.get_mode() == configuration.WS2801:
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]
        spi_port = configuration.CONFIG[configuration.SPI_PORT_KEY]
        spi_device = configuration.CONFIG[configuration.SPI_DEVICE_KEY]

        return ws2801.Ws2801Renderer(pixel_count, spi_port, spi_device)
    elif configuration.get_mode() == configuration.WS281x:
        pixel_count = configuration.CONFIG[configuration.PIXEL_COUNT_KEY]
        gpio_pin = configuration.CONFIG[configuration.GPIO_PIN_KEY]

        return ws281x.Ws281xRenderer(pixel_count, gpio_pin)
    elif configuration.get_mode() == configuration.PWM:
        return led_pwm.LedPwmRenderer(airport_render_config)
    else:
        # "Normal" LEDs
        return led.LedRenderer(airport_render_config)


renderer = get_test_renderer()

if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    safe_logging.safe_log(LOGGER, "Testing all colors for all airports.")

    # Test LEDS on startup
    colors_to_test = (
        weather.LOW,
        weather.RED,
        weather.YELLOW,
        weather.GREEN,
        weather.BLUE,
        weather.WHITE,
        weather.GRAY,
        weather.DARK_YELLOW,
        weather.OFF
    )

    for color in colors_to_test:
        safe_logging.safe_log(LOGGER, "Setting to {}".format(color))

        [renderer.set_led(airport_render_config[airport], colors[color])
            for airport in airport_render_config]

        renderer.show()

        time.sleep(0.5)

    safe_logging.safe_log(LOGGER, "Starting airport identification test")

    while True:
        for airport in airport_render_config:
            led_index = airport_render_config[airport]
            renderer.set_led(
                led_index,
                colors[weather.GREEN])

            renderer.show()

            safe_logging.safe_log(
                LOGGER,
                "LED {} - {} - Now lit".format(led_index, airport))

            input("Press Enter to continue...")

            renderer.set_led(
                airport_render_config[airport],
                colors[weather.OFF])

            renderer.show()

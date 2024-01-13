# Self-Test file that makes sure all
# off the wired lights are functional.

import time

import renderer
from configuration import configuration
from data_sources import weather
from lib import colors, safe_logging

airport_render_config = configuration.get_airport_configs()
rgb_colors = colors.get_colors()

renderer = renderer.get_renderer()

if __name__ == '__main__':
    # Start loading the METARs in the background
    # while going through the self-test
    safe_logging.safe_log("Testing all colors for all airports.")

    # Test LEDS on startup
    colors_to_test = (
        colors.MAGENTA,
        colors.RED,
        colors.YELLOW,
        colors.GREEN,
        colors.BLUE,
        colors.WHITE,
        colors.GRAY,
        colors.DARK_YELLOW,
        colors.OFF
    )

    for color in colors_to_test:
        safe_logging.safe_log("Setting to {}".format(color))

        renderer.set_all(rgb_colors[color])

        time.sleep(0.5)

    safe_logging.safe_log("Starting airport identification test")

    while True:
        for airport in airport_render_config:
            led_indices = airport_render_config[airport]

            for led_index in led_indices:
                renderer.set_led(
                    led_index,
                    rgb_colors[colors.GREEN])

                safe_logging.safe_log(
                    "LED {} - {} - Now lit".format(led_index, airport))

            renderer.show()

            input("Press Enter to continue...")

            renderer.set_leds(
                airport_render_config[airport],
                rgb_colors[weather.OFF])

            renderer.show()

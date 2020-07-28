"""
Handles controlling standard LEDs.
"""

import lib.local_debug as local_debug
from data_sources import weather

if local_debug.is_debug():
    from lib.local_debug import PWM
else:
    import RPi.GPIO as GPIO
    from RPi.GPIO import PWM


class LedRenderer(object):
    """
    Class that renders the airport data to LEDs connected to
    the GPIO pins using Pulse Width Modulation (PWM).
    """

    def set_all(
        self,
        color: list
    ):
        """
        Sets all of the leds to the same color.

        Args:
            color (list): The color we want to set all of the LEDs to.
        """

        for pin_set in self.__pins__:
            self.set_led(pin_set, color)

    def set_led(
        self,
        airport_pins,
        color
    ):
        """
        Sets the color of a LED based on the pins for that LED

        Arguments:
            pins {array of int} -- And array of the pins that control the LED
            color {array of int} -- The values to set each to for the colors.
        """

        if not local_debug.is_debug():
            GPIO.setup(airport_pins, GPIO.OUT)
            GPIO.output(airport_pins, color)

    def show(
        self
    ):
        # Here for interfacing/duck typing
        pass

    def __init__(
        self,
        airport_pins
    ):
        """
        Create a new PWM LED renderer.

        Arguments:
            airport_pins {dictionary} -- GPIO pins to PWM keyed by airport name.
        """

        self.__pins__ = airport_pins

        for airport in airport_pins:
            pins = airport_pins[airport]

            if not local_debug.is_debug():
                GPIO.setup(pins, GPIO.OUT)
                GPIO.output(pins, (0, 0, 0))

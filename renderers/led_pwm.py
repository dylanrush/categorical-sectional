"""
Handles controlling Pulse Width Modulation LEDs.
"""

import lib.local_debug as local_debug
from data_sources import weather

if local_debug.is_debug():
    from lib.local_debug import PWM
else:
    import RPi.GPIO as GPIO
    from RPi.GPIO import PWM


class LedPwmRenderer(object):
    """
    Class that renders the airport data to LEDs connected to
    the GPIO pins using Pulse Width Modulation (PWM).
    """

    def __create_pwm_for_pin__(self, pin_number):
        """
        Makes sure a PWM object exists for each pin.
        Creates and starts the pin if needed.

        Arguments:
            pin_number {int} -- The pin to create a PWM for.
        """

        if not pin_number in self.airport_pwm_matrix:
            self.airport_pwm_matrix[pin_number] = PWM(
                pin_number, self.pwm_frequency)
            self.airport_pwm_matrix[pin_number].start(0.0)

    def set_led(self, airport_pins, color):
        """
        Sets the color of an airport using LED/PWM
        
        Arguments:
            airport_pins {array of int} -- An array holding the pin used for R, G, B colors. In that order
            color {array} -- Three number array that corresponds to each RGB pin to set the PWM power to.
        """

        for pin_number in airport_pins:
            self.__create_pwm_for_pin__(pin_number)

        self.airport_pwm_matrix[airport_pins[0]].ChangeDutyCycle(color[0])
        self.airport_pwm_matrix[airport_pins[1]].ChangeDutyCycle(color[1])
        self.airport_pwm_matrix[airport_pins[2]].ChangeDutyCycle(color[2])

    def __init__(self, airport_pins):
        """
        Create a new PWM LED renderer.

        Arguments:
            airport_pins {dictionary} -- GPIO pins to PWM keyed by airport name.
        """

        self.pwm_frequency = 100.0
        self.airport_pwm_matrix = {}

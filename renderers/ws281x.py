"""
Simple driver of the WS281x addressable RGB LED lights, commonly called "NeoPixels"
Based on the AdaFruit example.
License: Public Domain
"""

from __future__ import division

import time

import board
import lib.local_debug as local_debug
import neopixel
from renderers.debug import Renderer


class Ws281xRenderer(Renderer):
    def __init__(
        self,
        pixel_count,
        gpio_pin,
        pixel_order
    ):
        """
        Create a new controller for the WS2801 based lights

        Arguments:
            pixel_count {int} -- The total number of neopixels.
            gpio_pin {int} -- The GPIO pin the WS281x data pin is on. This is IO addressing, NOT physical addressing.
            pixel_order {str} -- The RGB or GRB order that colors are provided in.
        """

        super().__init__(pixel_count)

        if not local_debug.is_debug():
            from adafruit_blinka.microcontroller.bcm283x.pin import Pin

            self.__leds__ = neopixel.NeoPixel(
                Pin(gpio_pin),  # board.D18, #gpio_pin,
                pixel_count,
                auto_write=False,
                pixel_order=pixel_order)

            # Clear all the pixels to turn them off.
            self.set_all([0, 0, 0])

    def set_all(
        self,
        color: list
    ):
        """
        Sets all of the leds to the same color.

        Args:
            color (list): The color we want to set all of the LEDs to.
        """

        self.__leds__.fill(color)
        self.__leds__.show()
        super().set_all(color)

    def set_led(
        self,
        pixel_index: int,
        color: list
    ):
        """
        Sets the given airport to the given color

        Arguments:
            pixel_index {int} -- The index of the pixel to set
            color {int array} -- The RGB (0-255) array of the color we want to set.
        """
        if pixel_index >= self.pixel_count:
            return

        if pixel_index < 0:
            return

        self.__leds__[pixel_index] = color
        super().set_led(pixel_index, color)

    def show(
        self
    ):
        self.__leds__.show()
        super().show()

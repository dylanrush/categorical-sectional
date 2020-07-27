"""
Simple driver of the WS281x addressable RGB LED lights, commonly called "NeoPixels"
Based on the AdaFruit example.
License: Public Domain
"""

from __future__ import division
import time

import lib.local_debug as local_debug

import board
import neopixel


class Ws281xRenderer(object):
    def __init__(
        self,
        pixel_count,
        gpio_pin
    ):
        """
        Create a new controller for the WS2801 based lights

        Arguments:
            pixel_count {int} -- The total number of neopixels.
            gpio_pin -- The GPIO pin the WS281x data pin is on. This is IO addressing, NOT physical addressing.
            spi_device {int} -- The SPI device on the port that the neopixels are on.
        """

        self.__pixel_count__ = pixel_count

        if not local_debug.is_debug():
            self.__pixels__ = neopixel.NeoPixel(
                board.D18, #gpio_pin,
                pixel_count,
                pixel_order=neopixel.RGB)

            # Clear all the pixels to turn them off.
            self.__pixels__.fill((0, 0, 0))

            self.__pixels__.show()

    def set_led(
        self,
        pixel_index: int,
        color
    ):
        """
        Sets the given airport to the given color

        Arguments:
            pixel_index {int} -- The index of the pixel to set
            color {int array} -- The RGB (0-255) array of the color we want to set.
        """
        if pixel_index >= self.__pixel_count__:
            return

        if pixel_index < 0:
            return

        if not local_debug.is_debug():
            self.__pixels__[pixel_index] = (color[0], color[1], color[2])
            self.__pixels__.show()

    def show(
        self
    ):
        self.__pixels__.show()

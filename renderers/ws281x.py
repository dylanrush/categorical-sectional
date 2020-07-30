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

#TODO - Add "Clear" function to all renderers
#TODO - Clear on visualizer switch


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
        """

        self.__pixel_count__ = pixel_count

        if not local_debug.is_debug():
            from adafruit_blinka.microcontroller.bcm283x.pin import Pin

            self.__pixels__ = neopixel.NeoPixel(
                Pin(gpio_pin), # board.D18, #gpio_pin,
                pixel_count,
                auto_write=False,
                pixel_order=neopixel.GRB)

            # Clear all the pixels to turn them off.
            self.__pixels__.fill((0, 0, 0))

            self.__pixels__.show()
        else:
            self.__pixels__ = range(pixel_count)
    
    def set_all(
        self,
        color: list
    ):
        """
        Sets all of the leds to the same color.

        Args:
            color (list): The color we want to set all of the LEDs to.
        """
        self.__pixels__.fill(color)
        self.__pixels__.show()

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
        if pixel_index >= self.__pixel_count__:
            return

        if pixel_index < 0:
            return

        self.__pixels__[pixel_index] = color

    def show(
        self
    ):
        self.__pixels__.show()

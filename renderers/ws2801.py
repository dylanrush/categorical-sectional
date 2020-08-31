"""
Simple driver of the WS2801/SPI-like addressable RGB LED lights.
Based on the AdaFruit code by Tony DiCola
License: Public Domain
"""

from __future__ import division

import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_WS2801
# Import the WS2801 module.
import lib.local_debug as local_debug
from renderers.debug import Renderer


class Ws2801Renderer(Renderer):
    def __init__(
        self,
        pixel_count,
        spi_port,
        spi_device
    ):
        """
        Create a new controller for the WS2801 based lights

        Arguments:
            pixel_count {int} -- The total number of neopixels. Probably a multiple of 25.
            spi_port {int} -- The SPI port the neopixels are on.
            spi_device {int} -- The SPI device on the port that the neopixels are on.
        """

        super().__init__(pixel_count)

        self.__leds__ = pixel_count

        if not local_debug.is_debug():
            # Specify a hardware SPI connection on /dev/spidev0.0:
            self.__leds__ = Adafruit_WS2801.WS2801Pixels(
                pixel_count,
                spi=SPI.SpiDev(spi_port, spi_device))

            # Clear all the pixels to turn them off.
            self.__leds__.clear()

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
        indices = range(self.pixel_count)
        ws2801_color = Adafruit_WS2801.RGB_to_color(
            color[0],
            color[1],
            color[2])

        [self.__leds__.set_pixel(index, ws2801_color)
            for index in indices]

        super().set_all(color)

        self.show()

    def set_led(
        self,
        pixel_index,
        color
    ):
        """
        Sets the given airport to the given color

        Arguments:
            pixel_index {int} -- The index of the pixel to set
            color {int array} -- The RGB (0-255) array of the color we want to set.
        """

        if (pixel_index < 0):
            return

        if (pixel_index >= self.pixel_count):
            return

        self.__leds__.set_pixel(
            pixel_index,
            Adafruit_WS2801.RGB_to_color(
                color[0],
                color[1],
                color[2]))

        super().set_led(pixel_index, color)

    def show(
        self
    ):
        self.__leds__.show()
        super().show()

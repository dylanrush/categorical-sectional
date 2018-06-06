# Simple demo of of the WS2801/SPI-like addressable RGB LED lights.
# Will animate a rainbow color cycle on all pixels.
# Based on the AdaFruit code by Tony DiCola
# License: Public Domain
from __future__ import division
import time

# Import the WS2801 module.
import lib.local_debug as local_debug

import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI


class Ws2801Renderer(object):
    def __init__(self, pixel_count, spi_port, spi_device):
        self.pixel_count = pixel_count

        if not local_debug.is_debug():
            # Specify a hardware SPI connection on /dev/spidev0.0:
            self.pixels = Adafruit_WS2801.WS2801Pixels(
                self.pixel_count, spi=SPI.SpiDev(spi_port, spi_device))

            # Clear all the pixels to turn them off.
            self.pixels.clear()
            self.pixels.show()  # Make sure to call show() after changing any pixels!

    def set_led(self, render_data, color):
        """
        Sets the given airport to the given color

        Arguments:
            pixel_index {int} -- The index of the pixel to set
            color {int array} -- The RGB (0-255) array of the color we want to set.
        """
        pixel_index = render_data[0]
        if not local_debug.is_debug():
            self.pixels.set_pixel(pixel_index, Adafruit_WS2801.RGB_to_color(
                color[0], color[1], color[2]))

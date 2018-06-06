# Simple demo of of the WS2801/SPI-like addressable RGB LED lights.
# Will animate a rainbow color cycle on all pixels.
# Author: Tony DiCola
# License: Public Domain
from __future__ import division
import time

# Import the WS2801 module.
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import configuration


# Configure the count of pixels:
PIXEL_COUNT = configuration.CONFIG['pixel_count']

# Specify a hardware SPI connection on /dev/spidev0.0:
SPI_PORT = configuration.CONFIG['spi_port']
SPI_DEVICE = configuration.CONFIG['spi_device']
pixels = Adafruit_WS2801.WS2801Pixels(
    PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# Clear all the pixels to turn them off.
pixels.clear()
pixels.show()  # Make sure to call show() after changing any pixels!

# Define the wheel function to interpolate between different hues.


def wheel(pos):
    if pos < 85:
        return Adafruit_WS2801.RGB_to_color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Adafruit_WS2801.RGB_to_color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Adafruit_WS2801.RGB_to_color(0, pos * 3, 255 - pos * 3)

# Define rainbow cycle function to do a cycle of all hues.


def set_all(r, g, b):
    """
    Sets all of the pixels to the given RGB color

    Arguments:
        r {int} -- RED value : 0 to 255
        g {int} -- GREEN value : 0 to 255
        b {int} -- BLUE value : 0 to 255
    """

    for i in range(pixels.count()):
        pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(r, g, b))
        pixels.show()


def rainbow_cycle(pixels, wait=0):
    for j in range(256):  # one cycle of all 256 colors in the wheel
        for i in range(pixels.count()):
            # tricky math! we use each pixel as a fraction of the full 96-color wheel
            # (thats the i / strip.numPixels() part)
            # Then add in j which makes the colors go around per pixel
            # the % 96 is to make the wheel cycle around
            pixels.set_pixel(i, wheel(((i * 256 // pixels.count()) + j) % 256))
        pixels.show()
        if wait > 0:
            time.sleep(wait)


print('Initializing ...')
set_all(0, 0, 0)
print('Rainbow cycling, press Ctrl-C to quit...')

# Make the rainbow move at a different cycle
# so it speeds up and slows down
min_wait = 0.0
max_wait = 0.2
wait_step = 0.01
wait_direction = 1

wait = min_wait
while True:
    rainbow_cycle(pixels, wait)

    wait += (wait_direction * wait_step)

    if wait > max_wait:
        wait = max_wait
        wait_direction = -1.0
    elif wait < min_wait:
        wait = min_wait
        wait_direction = 1.0

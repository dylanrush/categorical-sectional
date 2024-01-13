# Simple test for NeoPixels on Raspberry Pi

import sys
import time

from lib.local_debug import IS_PI

if not IS_PI:
    print("This utility can only be run on the Raspberry Pi")
    sys.exit()

import board
import neopixel

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 100

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, auto_write=False, pixel_order=ORDER
)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)


print("Starting primary color and dimming test")

for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
    for proportion in [255, 128, 64, 32, 16, 8, 4, 2, 0]:
        adjustment = proportion / 255.0

        print("Adjusting {} to {}".format(color, adjustment))

        final_color = []

        for component in color:
            final_color.append(int(component * adjustment))

        print("Final color is {}".format(final_color))

        pixels.fill(tuple(final_color))
        pixels.show()

        time.sleep(1)

print("Starting color cycle test")

while True:
    rainbow_cycle(0.001)  # rainbow cycle with 1ms delay per step

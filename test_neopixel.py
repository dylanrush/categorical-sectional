import board
import neopixel
pixels = neopixel.NeoPixel(board.D18, 50, pixel_order=neopixel.RGB)

pixels.fill((255, 0, 0))
pixels.show()

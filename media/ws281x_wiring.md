# WS281x Wiring

## Summary

This file will guide you through wiring a WS2811, WS2812, or similar based LED system. These are also known by the tradename "NeoPixel" from AdaFruit.

## Wiring the Strand

Most WS281x based strands will have plugs to join them together. Please be aware of the power limits for the number of pixels you are using. Choose a power supply appropriately, and in some cases you may need to use multiple power supplies.


## Level Shifting

Due to the Raspberry Pi using a 3V system for communication and teh WS281x series using 5V, you will need to include what is known as a "Level Shifter".

In this case, you will want a [74AHCT125](https://www.amazon.com/Adafruit-Accessories-Quad-Level-Shifter-piece/dp/B00XW2L39K/ref=sr_1_1?dchild=1&keywords=74AHCT125&qid=1606100641&sr=8-1). This can be found on Amazon for about $6.


## Wiring Everything Together

It is highly reccomended to use the wiring tutoruial from [AdaFruit](https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring)

![wiring details](https://cdn-learn.adafruit.com/assets/assets/000/064/121/original/led_strips_raspi_NeoPixel_Level_Shifted_bb.jpg?1540314807)


You may use a large piece of shrink wrap over the logic converter chip to protect the solder joints and prevent shorts.


- Pi GPIO18 (physical pin 12) to 74AHCT125 pin 1A
- 74AHCT125 pin 1Y to NeoPixel DIN
- Power supply ground to 74AHCT125 ground
- Power supply ground to 74AHCT125 pin 1OE
- Power supply ground to Pi GND
- Power supply ground to NeoPixel GND
- Power supply 5V to 74AHCT125 VCC
- Power supply 5V to NeoPixel 5V.
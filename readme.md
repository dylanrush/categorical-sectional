

## Parts List

Description | Cost | Link
------------|:-----|:-----
Raspberry Pi Zero W | $29.99 | https://www.amazon.com/CanaKit-Raspberry-Wireless-Starter-Official/dp/B06XJQV162/ref=sr_1_7?s=electronics&ie=UTF8&qid=1528557992&sr=1-7&keywords=raspberry+pi+zero+w
5 volt, 4 amp power supply | $12.99 | https://www.amazon.com/gp/product/B00MRGKPH8/ref=oh_aui_detailpage_o06_s00?ie=UTF8&psc=1
Barrel jack adapters | $7.99 | https://www.amazon.com/gp/product/B01M4RBARQ/ref=oh_aui_detailpage_o06_s01?ie=UTF8&psc=1
Individually addressable LEDs (WS2801 based) | $39.95 | https://www.amazon.com/12mm-Diffused-Digital-Pixels-Strand/dp/B073MZWBYS/ref=sr_1_1?ie=UTF8&qid=1528558371&sr=8-1&keywords=adafruit+ws2801
4 Pin JST SM Plugs | $7.99 | https://www.amazon.com/Visdoll-Pairs-Female-Connector-Cable/dp/B075K48BD9/ref=sr_1_8?ie=UTF8&qid=1528559351&sr=8-8&keywords=4+Pin+JST+SM+Plug

## Python Package Install
From a terminal on the Raspberry Pi

```bash
sudo pip install Adafruit-GPIO
```

```bash
sudo pip install RPi-GPIO
```

```bash
sudo pip install pytest
```

```bash
sudo pip install Adafruit_WS2801
```

## Raspberry Pi Settings

Run 'raspi-config' and enable the SPI bus under Advanced

```bash
sudo raspi-config
```

# Wiring the WS2801

https://learn.adafruit.com/12mm-led-pixels/wiring
https://tutorials-raspberrypi.com/how-to-control-a-raspberry-pi-ws2801-rgb-led-strip/

## The Barrel Jack Adapter

For the barrel jack, use the two thinner wires that come out of the top of the plastic connector from the LED lights.

One is red, the other blue.

* Blue -> Barrel jack minus
* Red -> Barrel jack positive

## The Raspberry Pi

Use the group of four wires from a *_male_* JST SM adapter.

Solder them to the board.

* Blue -> Tied off and shrink wrapped. Not connected.
* Red -> Raspberry Pi 3V Pin 17 (Physical)
* Yellow -> Pin 19(Physical)/SPI MOSI
* Green -> Pin 23(Physical)/SCLK/SPI

## Connect the Male JST and LED connectors together.

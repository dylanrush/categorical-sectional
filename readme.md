# VFR Light Map

This is a fork of Dylan Rush's excellent "[Categorical-Sectional](https://github.com/dylanrush/categorical-sectional)".

The purpose of this version was to unify the control code of different LED light types and to add support for WS2801 "individually" addressible LED lights.

I have also attempted to make setup easier by moving the LED configuration into data files.

![Seattle to Oshkosh, showing Sunset across the country](media/weather_and_fade.jpg)

## What You Need

### Skills Required

To complete this project you will need to:

- Edit two text files.
- Solder three wires.

### Additional Hardware

The instructions given here are for WS2801 LED based strands, such as those found on AdaFruit.

The electronics cost about \$90 USD if you are buying everything new, and want 50 lights.

To complete the project you will need to supply your own chart and backing board.

Soldering is required for three (3) wires, along with some electrical tape.

To finish the installation you will need a monitor, and a keyboard.

#### Other Raspberry Pis

A parts manifest lists a Raspberry Pi Zero due to its size and lower power consumption, but a spare 2 or 3 will work as long as it has WiFi. The wiring diagram does not change.

## Setup

### Parts List

Description                                  | Cost    | Link
-------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
Raspberry Pi Zero W                          | \$29.99 | <https://www.amazon.com/CanaKit-Raspberry-Wireless-Starter-Official/dp/B06XJQV162/ref=sr_1_7?s=electronics&ie=UTF8&qid=1528557992&sr=1-7&keywords=raspberry+pi+zero+w>
5 volt, 4 amp power supply                   | \$12.99 | <https://www.amazon.com/gp/product/B00MRGKPH8/ref=oh_aui_detailpage_o06_s00?ie=UTF8&psc=1>
Barrel jack adapters                         | \$7.99  | <https://www.amazon.com/gp/product/B01M4RBARQ/ref=oh_aui_detailpage_o06_s01?ie=UTF8&psc=1>
Individually addressable LEDs (WS2801 based) | \$39.95 | <https://www.amazon.com/12mm-Diffused-Digital-Pixels-Strand/dp/B073MZWBYS/ref=sr_1_1?ie=UTF8&qid=1528558371&sr=8-1&keywords=adafruit+ws2801>
4 Pin JST SM Plugs                           | \$7.99  | <https://www.amazon.com/Visdoll-Pairs-Female-Connector-Cable/dp/B075K48BD9/ref=sr_1_8?ie=UTF8&qid=1528559351&sr=8-8&keywords=4+Pin+JST+SM+Plug>

### Upgrade Instructions

If you have an older version of the software (V1.6 or earlier), it is highly recommended that you copy your configuration files into the user configuration directory.

The user configuration files and directory are explained in the `~/weather_map/config.json` section.

If you have not already migrated to a version that has the user configuration files, open a command line on the Raspberry Pi and execute the following commands:

```bash
cd ~/categorical-sectional
mkdir ~/weather_map
cp data/*.json ~/weather_map/
```

Please note that you may need to modify the value of `"airports_file"`. You will most like need to replace the `data/` portion with `~/weather_map/`

For example: `"airports_file": "data/kawo_to_kosh.json"` would become `"airports_file": "~/weather_map/kawo_to_kosh.json"`

Once you have performed this backup process and are sure that your files are in the new location, you may update the software.

**WARNING**: The following steps will discard any modifications you have performed.

```bash
cd ~/categorical-sectional
git fetch
git reset --hard HEAD
git checkout master
git pull
```

### Bootstrapping The Raspberry Pi

#### OS Installation

This section gets you started with installing the software.

A full tutorial on how to install the Operating System is available at: <https://www.raspberrypi.org/documentation/installation/noobs.md>

1. Boot the Raspberry Pi with the empty SD card.
2. You will be given a choice of operating systems to install. You will also be asked for your WiFi network and password.
3. Choose the WiFi network that will be used when the project is completed.
4. Choose "Raspbian" as the operating system.
5. When it is finished, login with the username:pi password:raspberry

#### Get The Code

From the command line, after logging in:

```bash
cd ~
git clone https://github.com/JohnMarzulli/categorical-sectional.git
```

This will install this software onto the Raspberry Pi.

#### Python Package Install

From a terminal on the Raspberry Pi

```bash
cd ~/categorical-sectional
sudo python3 setup.py develop
```

#### Raspberry Pi Settings

Run 'raspi-config' and enable the SPI bus under Advanced

```bash
sudo raspi-config
```

## Wiring

### Wiring the WS2801

If you are using multiple strands of lights, plug them together. Tape off the red and blue tap wires between the connectors and at the end of the strand.

Leave the read and blue wire at the start of the strand for the moment.

### The Barrel Jack Adapter

For the barrel jack, use the two thinner wires that come out of the top of the plastic connector from the LED lights.

One is red, the other blue.

- Blue -> Barrel jack minus
- Red -> Barrel jack positive

#### Wiring Detail For Barrel Jack

![barrel jack wiring details](media/barrel_jack.jpg)

### The Raspberry Pi

Use the group of four wires from a **male** JST SM adapter.

Solder them to the board.

Wire Color | Physical Pin                                | Pin Name
---------- | ------------------------------------------- | -------------
Blue       | Tied off and shrink wrapped. Not connected. | Not connected
Red        | 25                                          | GRND
Black      | 23                                          | SCLK
Green/Teal | 19                                          | MOSI

#### Wiring Detail From Top

![Pi Wiring From Top](media/pins_from_top.jpg)

#### Wiring Detail From Bottom

![Pi Wiring From Bottom](media/pins_from_bottom.jpg)

## Final Assembly

- Connect the Male JST and LED connectors together.
- Connect the barrel jack into the Neopixel strip.
- Add the SD card to the Pi.
- Plug in the NeoPixels first, then the Raspberry Pi.

## Understanding The Configuration Files

All of the configuration files with the **default** values will be in the "data" sub directory.

Unless you are building the same exact map that I did (Puget Sound to Oshkosh), then you will want to modify at least one of these values.

To help separate changes you make to personalize the map, you may create a user directory to holds values that override the defaults.

You will need to create a directory that branches from your home folder. This home folder has the special shortcut in Unix-like operating systems of `~`

To create this directory use the following command from a command line.

```bash
mkdir ~/weather_map
```

If you are using the default user of `pi`, then the full name of this directory is `/user/home/pi/weather_map/`.

### ~/weather_map/config.json

This is the first file loaded. It tells the software what type of lights are being used, and which airport file to open.

You do not need to include ALL of these values. Any values provided in this file OVERRIDE the default values. This shows what the defaults are.

```json
{
  "mode": "ws2801",
  "pixel_count": 50,
  "spi_device": 0,
  "spi_port": 0,
  "pwm_frequency": 100,
  "airports_file": "data/kawo_to_kosh.json",
  "blink_old_stations": true,
  "night_lights": true,
  "night_populated_yellow": false,
  "night_category_proportion": 0.05,
  "brightness_proportion": 1.0
}
```

Note: If you create your own mapping file for the LEDs, the `~/weather_map` directory is the best place to put it.

Here is an example of using overriding values:

```json
{
  "airports_file": "~/weather_map/puget_sound_region.json",
  "blink_old_stations": false,
  "night_category_proportion": 0.10,
  "brightness_proportion": 0.5
}
```

In this example we are using the file `puget_sound_region.json` to define our mapping. This file is expected to be in the `/home/pi/weather_map` folder. We are also reducing the overall brightness (ever during the day) by 50% of what the lights are capable of.

#### blink_old_stations

Set this to `false` if you would like the stations to remain the last known category/color even if the data is old.

The default is `true`. When the value is set to `true` any station with data older than 90 minutes will start blinking to indicate that the data is old.

When new data is received that has an issue date less than 90 minutes from the current time, then the light will stop blinking.

#### night_lights

Set this to `true` if you would like the weather stations to change colors based on the time of day.

If you are using WS2801 or PWM based lights, then this is a gradual process.

First the light will fade from the flight condition color to a bright yellow to indicate "Populated night". As the station gets darker, the light fades to a darker yellow by the time the station is "pitch black" in night.

In the morning, the light will increase back to a bright yellow as the office sunrise time approaches. As the station approaches full daylight, the light will fade from bright yellow to the color appropriate for the flight condition.

#### night_populated_yellow

Set this to `true` if you would like the day/night transition to show stations that are currently in "full dark" using yellow.

This will transition/fade into yellow from the standard category color.

Setting this to `false` will result in the category color fading. The amount the category fades is determined by `night_category_proportion`

#### night_category_proportion

This is only used when `night_populated_yellow` is set to `false`.

The default value is `0.05`, or 5%. This means that when the station is in "full dark" that the normal category color will be reduced to 5% of the normal strength.

This creates a pleasant fade as stations on the chart transition from day to night, back to day.

_NOTE:_ This will not work with standard mode GPIO based LEDs.

#### brightness_proportion

This an adjustment to the LED brightness. It is applied AFTER all other light calculations are performed.

The intent is to provide a way to dim the LEDs during daylight hours.

This is a proportion

- `0.0` will result in all lights effectively being turned off.
- `0.5` will result in the lights being half as bright.
- `1.0` will result in no change.

You may need to adjust `night_category_proportion` if you use this value. A low enough value of `brightness_proportion` may result in LEDs for stations in the dark to result in not being visible. Increasing `night_category_proportion` will result in the LEDs being turned on again.

#### mode

This controls which type of LED system to use for controlling the lights.

Value  | Description
------ | ------------------------------------------------------------------------------------------------
ws2801 | Use WS2801 based light strands like those from AdaFruit
pwm    | Use pulse width modulation based LEDs. This can have their colors changed more than normal LEDs.
led    | Use standard LEDs that have a positive wire for each color and a common ground.

#### pixel_count

If you are using ws2801 based LEDs then you may need to change "pixel_count". Each strand will come with a numbe rof LEDs. You you are using a single strand, then set this number to that count. If you have combined strands, then set the total number of lights.

#### spi_device and spi_port

You will probably not need to change this. If you do need to change this, then you probably know what to do.

#### pwm_frequency

Used if you are using PWM LEDs.

#### airports_file

This is the file that contains the airport names and the wiring configuration for them.

### Airports File

#### Annotated Example File

This shows the two sections for an example airport file.

```json
{
  "pwm": [
    { "KRNT": [3, 5, 7] },
    { "KSEA": [11, 13, 15] },
    { "KPLU": [19, 21, 23] },
    { "KOLM": [29, 31, 33] },
    { "KTIW": [32, 35, 37] },
    { "KPWT": [36, 38, 40] },
    { "KSHN": [8, 10, 12] }
  ],
  "ws2801": [
    { "KRNT": { "neopixel": 0 } },
    { "KSEA": { "neopixel": 2 } },
    { "KPLU": { "neopixel": 4 } },
    { "KOLM": { "neopixel": 6 } },
    { "KTIW": { "neopixel": 8 } },
    { "KPWT": { "neopixel": 10 } },
    { "KSHN": { "neopixel": 12 } }
  ]
}
```

#### Explanation

There are two sections:

##### pwm

Contains the airport name and wiring information. The first number is the wire controlling the red LED, then the green LED, and finally the blue LED.

These wire numbers refer to the **physical** board number on the Raspberry pie.

So for KRNT (Renton), the wire leading to the Red LED would be wired to the GPIO board at pin 3\. The Blue LED would be wired to pin 5, and the green LED wire would be wired to pin 7.

_NOTE:_ The "pwm" section is used by both the normal LEDs and the pulse width controlled LEDs.

##### ws2801

This section contains the information required to control a strand of WS2801 lights.

Once again, this starts with an airport or weather station identifier.

Next to contains a "neopixel" identifier. This is the order of the light on the strand.

_NOTE:_ The first light is "0", the second light is "1".

Due to the way your lights may need to be arranged to fit on the map, some lights may need to be skipped, so keep track of your lights.

##### Illustration of Numbering

Using the first few lines of the ws2801 section from above, this shows how the numbering works.

This project uses "zero based indexing".

In this scenario the second and fourth light are not used. They will remain off the entire time.

The first light is assigned to Renton airport. The third light will show SeaTac aiport.

```code
[Pi] ------[LED]------[LED]------[LED]------[LED]

           0/KRNT    Skipped     2/KSEA    Skipped
```

## Testing The LED Wiring

There is a self-test file included to help quickly validate your wiring. This works for both WS2801 and LED based maps.

This file exercises the LED lights without having to wait for the entire mapping software to initialize.

You may use it from a bash command-line:

```bash
cd ~
cd categorical-sectional
python3 check_lights_wiring.py
```

Please note that this will only run on a Raspberry Pi.

Also note that you will need to run this from a command terminal and that the self-check will run in a loop until stopped. From a terminal you may use `ctrl+c` to stop the task.

This self-test runs in two phases:

1. All of the lights will cycle through all of the active colors. Any lights that do not turn on may not be configured properly or may not be wired correctly.
2. All lights will turn off. The tool will tell you which LED is turned on (by number, starting a `0`), along with the station identifier currently set in the configuration. The tool will then prompt you to press `{enter}` to move to the next light.

Please do not run the test WHILE the map code is running. Mutliple programs attempting to control the lights will produce unexpected results.

## Testing The Station Configuration

There is a self-test file included to help quickly validate your configuration files.

You may use it from a bash command-line:

```bash
cd ~
cd categorical-sectional
python3 check_config_files_wiring.py
```

This tool may be also run from a Windows, Linux, or Mac based machine.

It checks each weather station in your configuration.

Each station is:

- Checked against the FAA CSV file to validate the ICAO code.
- Checked to validate the civil twilight information can be fetched.
- Checked that a METAR can be retrieved.

Any failures will list the identifier code and the reason.

Not being able to fetch a weather report is not considered a fatal error if other data can be obtained. Any airport that had issues fetching weather will be listed, and may simply be temporarily down.

## Running It At Boot

To run it at boot, perform the following steps:

1. Log into the device as the user "pi" with password "raspberry".
2. Type "crontab -e"
3. Select "Nano" (Option 1)
4. Enter the following text at the _bottom_ of the file:

  ```code
  @reboot python3 /home/pi/categorical-sectional/controller.py &
  ```

5. Save the file and exit.
6. sudo reboot now

Capitalization counts. The map lights should come on with each boot now.

## Installing Node & Optional Config Server

Installing the remote control is optional.

To be able to reach the web controls you may need to change settings in your home router.
Each router or modem will be different, but you may have the option to give a name to your WeatherMap device.
This will allow you to reach your map by visiting http://weathermap

1. `wget https://nodejs.org/dist/v11.15.0/node-v11.15.0-linux-armv6l.tar.gz`
1. `tar -xzf node-v11.15.0-linux-armv6l.tar.gz`
1. `sudo cp -R node-v11.15.0-linux-armv6l/* /usr/local/`
1. `sudo ln -s /usr/local/bin/node /usr/bin/node`
1. `cd ~/categorical-sectional/MapConfig`
1. `npm install`
1. `node /home/pi/categorical-sectional/MapConfig/build/index.js`
1. `sudo raspi-config`
1. "Network  Options" -> "Hostname" -> "OK"
1. Set the name to `weathermap`
1. `crontab -e`
1. Add a new line that reads `https://www.youtube.com/watch?v=JN8A2nIMUWA`
1. Save and quit.

You may now open a browser on another computer, or even you phone, and visit http://weathermap

From there you may adjust the map's brightness, the night time behavior, and more.

## Colors

This project uses "standard" airport coloring for flight rules category, along with some unique colors.

Flight Rule | WS2801         | PWM            | LED
----------- | -------------- | -------------- | --------------
VFR         | Solid green    | Solid green    | Solid green
MVFR        | Solid blue     | Solid blue     | Solid blue
IFR         | Solid red      | Solid red      | Solid red
LIFR        | Solid magenta  | Solid magenta  | Blinking red
Smoke       | Solid gray     | Solid gray     | Solid gray
Night       | Solid yellow   | Solid yellow   | Solid yellow
Error       | Blinking white | Blinking white | Blinking white

## Apendix

<https://learn.adafruit.com/12mm-led-pixels/wiring> <https://tutorials-raspberrypi.com/how-to-control-a-raspberry-pi-ws2801-rgb-led-strip/> <https://www.raspberrypi.org/documentation/linux/usage/cron.md>

## Version History

Version | Change
------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
2.0     | Add a remote control app that allows for brightness, night effects, and more to be changed on the fly. Add support for WS2811 and WS2812 based lights. Major performance improvements for adressable RGB LEDs. Selectable visualizers.
1.10    | Add service that allows the configuration to be updated remotely without using the command line.
1.9     | Add documentation about the upgrade process for existing installations. Add configuration to control if old data causes a light to blink or not.
1.8     | Use the configuration files provided as a default base, and then source user configuration from the user directory.
1.7     | Allow for the brightness of the lights to be dimmed. This affects both the daytime and nighttime colors.
1.6     | Updated documentation, wiring self-check file that uses the configuration to exercise each weather station for all colors.
1.5     | New options that expand the day/night lighting cycle. Allows for dimmed category colors to be used instead of "night yellow.
1.4     | Changes to map initialization to help with bad airport identifiers. Improve handling of mismatch between four and three letter long identifiers when determining day/night cycle.
1.3     | Performance improvements.
1.2     | Migrated to Python 3.x
1.1     | Day / Night cycle.
1.0     | First release with addressable lights.

## Credits

Airport Location data from <http://ourairports.com/data/> Airport sunrise/sunset data from <https://sunrise-sunset.org/api>

## License

This project is covered by the GPL v3 liscense.

Please see

<liscense.md>
</liscense.md>

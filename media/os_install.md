# Bootstrapping The Raspberry Pi

## OS Installation

This section gets you started with installing the software.

A full tutorial on how to install the Operating System is available at: <https://www.raspberrypi.org/documentation/installation/noobs.md>

1. Boot the Raspberry Pi with the empty SD card.
2. You will be given a choice of operating systems to install. You will also be asked for your WiFi network and password.
3. Choose the WiFi network that will be used when the project is completed.
4. Choose "Raspbian" as the operating system.
5. When it is finished, login with the username:pi password:raspberry
 
### Raspberry Pi OS - Buster

For "Buster" versions, there is an issue with a key piece of communication software used for WS2801 based maps.

Please note that this issue **DOES NOT** exist for Ubuntu 20.10 For Arm. If you are using Ubunutu, then you will not need to perform these steps. You also do not need to perform these steps if you are using WS281x based lights.

From a terminal prompt on the Pi, please execute the following commands:

1. pip3 install spidev==3.4 --force-reinstall
2. sudo apt install nodejs
3. sudo apt install npm

## Installing The WeatherMap Code

From the command line, after logging in:

```bash
cd ~
git clone https://github.com/JohnMarzulli/categorical-sectional.git
```

This will install this software onto the Raspberry Pi.

## Installing The Python Packages

From a terminal on the Raspberry Pi

```bash
sudo apt install rng-tools
sudo apt install haveged
cd ~/categorical-sectional
sudo python3 setup.py develop
```

## Configure The Raspberry Pi

Run 'raspi-config' and enable the SPI bus under Advanced

```bash
sudo raspi-config
```

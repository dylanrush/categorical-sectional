"""
Module to help with mocking/bypassing
RaspberryPi specific code to enable for
debugging on a Mac or Windows host.
"""

from sys import platform


def is_debug():
    """
    returns True if this should be run as a local debug (Mac or Windows).
    """

    return platform in ["win32", "darwin"]


class PWM:
    """
    Mock class that allows the logic of the pwm controller to be run on Windows or Mac

    """

    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency

    def start(self, freq):
        """
        Starts the pulse-width-modulation for the pin at the given frequency.

        Arguments:
            freq {float} -- How often the pin should be given voltage.
        """

        print "Pin " + str(self.pin) + ' started with ' + str(freq)

    def ChangeDutyCycle(self, cycle):
        """
        Changes the cycle of a pin.

        Arguments:
            cycle {float} -- How often the pin should be given voltage.
        """

        print "Pin " + str(self.pin) + ' changing duty cycle to ' + str(cycle)

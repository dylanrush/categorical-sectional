"""
Module to help with mocking/bypassing
RaspberryPi specific code to enable for
debugging on a Mac or Windows host.
"""

from sys import platform, version_info
from sys import platform as os_platform
import platform

REQUIRED_PYTHON_MAJOR_VERSION = 3
REQUIRED_PYTHON_REVISION_VERSION = 5

IS_LINUX = 'linux' in os_platform
DETECTED_CPU = platform.machine()
IS_PI = "arm" in DETECTED_CPU


def validate_python_version():
    """
    Checks to make sure that the correct version of Python is being used.

    Raises:
        Exception -- If the  version of Python is not new enough.
    """

    error_text = None

    if REQUIRED_PYTHON_MAJOR_VERSION != version_info.major:
        error_text = 'Requires Python 3.x, found {}.x'.format(version_info.major)

    if REQUIRED_PYTHON_REVISION_VERSION > version_info.minor:
        error_text = 'Requires Python 3.5 or newer, found 3.{}'.format(version_info.minor)

    if error_text != None:
        print(error_text)
        raise Exception(error_text)

def is_debug():
    """
    returns True if this should be run as a local debug (Mac or Windows).
    """

    return os_platform in ["win32", "darwin"] or (IS_LINUX and not IS_PI)


validate_python_version()

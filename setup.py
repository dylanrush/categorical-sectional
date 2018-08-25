import lib.local_debug as local_debug
from setuptools import setup

installs = ['pytest',
            'Adafruit_WS2801',
            'requests']

if not local_debug.is_debug():
    installs.append('RPi.GPIO')

setup(name='cateorical-sectional',
      version='1.0',
      python_requires='>=3.5',
      description='VFR weathermap supporting Adafruit WS2801 lights.',
      url='https://github.com/JohnMarzulli/categorical-sectional',
      author='John Marzulli',
      author_email='john.marzulli@hotmail.com',
      license='GPL V3',
      install_requires=installs
      )

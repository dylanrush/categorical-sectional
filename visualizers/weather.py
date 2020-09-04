import lib.colors as colors_lib
from configuration import configuration
from data_sources import weather
from lib.logger import Logger
from renderers.debug import Renderer
from visualizers.visualizer import BlinkingVisualizer, rgb_colors


def celsius_to_fahrenheit(
    temperature_celsius: float
):
    if temperature_celsius is None:
        return 0

    return (temperature_celsius * (9.0 / 5.0)) + 32.0


def get_proportion_between_floats(
    start: float,
    current: float,
    end: float
):
    """
    Gets the "distance" (0.0 to 1.0) between the start and the end where the current is.
    IE:
        If the Current is the same as Start, then the result will be 0.0
        If the Current is the same as the End, then the result will be 1.0
        If the Current is halfway between Start and End, then the result will be 0.5


    Arguments:
        start {float} -- The starting temp.
        current {float} -- The temp we want to get the proportion for.
        end {float} -- The end temp to calculate the interpolaton for.

    Returns:
        float -- The amount of interpolaton for Current between Start and End
    """

    total_delta = (end - start)
    time_in = (current - start)

    return time_in / total_delta


def get_color_by_temperature_celsius(
    temperature_celsius: float
) -> list:
    colors_by_name = colors_lib.get_colors()

    if temperature_celsius is None:
        return colors_by_name[colors_lib.OFF]

    temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)

    if temperature_fahrenheit < 0:
        return colors_by_name[colors_lib.PURPLE]

    if temperature_fahrenheit < 20:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.PURPLE],
            colors_by_name[colors_lib.BLUE],
            get_proportion_between_floats(
                0,
                temperature_fahrenheit,
                20))

    if temperature_fahrenheit < 40:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.BLUE],
            colors_by_name[colors_lib.GREEN],
            get_proportion_between_floats(
                20,
                temperature_fahrenheit,
                40))

    if temperature_fahrenheit < 60:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.GREEN],
            colors_by_name[colors_lib.YELLOW],
            get_proportion_between_floats(
                40,
                temperature_fahrenheit,
                60))

    if temperature_fahrenheit < 80:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.YELLOW],
            colors_by_name[colors_lib.ORANGE],
            get_proportion_between_floats(
                60,
                temperature_fahrenheit,
                80))

    if temperature_fahrenheit < 100:
        return colors_lib.get_color_mix(
            colors_by_name[colors_lib.ORANGE],
            colors_by_name[colors_lib.RED],
            get_proportion_between_floats(
                80,
                temperature_fahrenheit,
                100))

    return colors_by_name[colors_lib.RED]


def get_color_by_precipitation(
    precipitation: str
) -> (list, bool):
    colors_by_name = colors_lib.get_colors()

    if precipitation is None:
        return (colors_by_name[colors_lib.GRAY], False)

    if precipitation is weather.DRIZZLE:
        return (colors_by_name[colors_lib.LIGHT_BLUE], False)

    if weather.RAIN in precipitation:
        return (colors_by_name[colors_lib.BLUE], precipitation is weather.HEAVY_RAIN)

    if precipitation is weather.SNOW:
        return (colors_by_name[colors_lib.WHITE], False)

    if precipitation is weather.ICE:
        return (colors_by_name[colors_lib.LIGHT_GRAY], True)

    if precipitation is weather.UNKNOWN:
        return (colors_by_name[colors_lib.PURPLE], False)

    return (colors_by_name[colors_lib.GRAY], False)


def get_color_by_pressure(
    inches_of_mercury: str
) -> list:
    high_pressure = 31.2
    # Standard pressure is 29.92,
    # so the upper limits were picked with
    # the standard value in the middle.
    #
    # The "high pressure" value was picked
    # based on what people perceive to be high pressure
    # and from that the low pressure value was picked.
    low_pressure = 28.64

    colors_by_name = colors_lib.get_colors()

    if inches_of_mercury is None:
        return colors_by_name[colors_lib.OFF]

    if inches_of_mercury < low_pressure:
        return colors_by_name[colors_lib.RED]

    if inches_of_mercury > high_pressure:
        return colors_by_name[colors_lib.BLUE]

    return colors_lib.get_color_mix(
        colors_by_name[colors_lib.RED],
        colors_by_name[colors_lib.BLUE],
        get_proportion_between_floats(
            low_pressure,
            inches_of_mercury,
            high_pressure))


class TemperatureVisualizer(BlinkingVisualizer):
    def __init__(
        self,
        renderer: Renderer,
        stations: dict,
        logger: Logger
    ):
        super().__init__(renderer, stations, logger)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders an airport.

        Arguments:
            airport {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station, self.__logger__)
        temperature = weather.get_temperature(metar)
        color_to_render = get_color_by_temperature_celsius(temperature)
        final_color = self.__get_brightness_adjusted_color__(
            station,
            color_to_render)

        self.__renderer__.set_led(
            self.__stations__[station],
            final_color)


class PrecipitationVisualizer(BlinkingVisualizer):

    def __init__(
        self,
        renderer: Renderer,
        stations: dict,
        logger: Logger
    ):
        super().__init__(renderer, stations, logger)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders a station based on any precipitation found in the metar.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station, self.__logger__)
        precipitation = weather.get_precipitation(metar)
        color_to_render, blink = get_color_by_precipitation(precipitation)
        final_color = self.__get_brightness_adjusted_color__(
            station,
            color_to_render)

        # Turn the LED off for the blink
        if is_blink and blink:
            final_color = colors_lib.get_brightness_adjusted_color(
                final_color, 0.0)

        self.__renderer__.set_led(
            self.__stations__[station],
            final_color)


class PressureVisualizer(BlinkingVisualizer):
    """
    Visualizer for pressure. High pressure is represented
    by BLUE while low pressure is represented by RED.
    """

    def __init__(
        self,
        renderer: Renderer,
        stations: dict,
        logger: Logger
    ):
        super().__init__(renderer, stations, logger)

    def render_station(
        self,
        station: str,
        is_blink: bool = False
    ):
        """
        Renders a station based on the pressure.

        Arguments:
            station {string} -- The identifier of the station.
        """

        metar = weather.get_metar(station, self.__logger__)
        pressure = weather.get_pressure(metar)
        color_to_render = get_color_by_pressure(pressure)
        final_color = self.__get_brightness_adjusted_color__(
            station,
            color_to_render)

        self.__renderer__.set_led(
            self.__stations__[station],
            final_color)

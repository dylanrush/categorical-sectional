from lib.logger import LOGGER
from renderers.debug import Renderer
from visualizers import flight_rules, rainbow, weather


class VisualizerManager(object):
    __VISUALIZERS__ = None

    @staticmethod
    def get_visualizers() -> list:
        return VisualizerManager.__VISUALIZERS__

    @staticmethod
    def initialize_visualizers(
        renderer: Renderer,
        stations: dict
    ) -> list:
        if VisualizerManager.__VISUALIZERS__ is not None:
            return

        VisualizerManager.__VISUALIZERS__ = [
            flight_rules.FlightRulesVisualizer(renderer, stations, LOGGER),
            weather.TemperatureVisualizer(renderer, stations, LOGGER),
            weather.PrecipitationVisualizer(renderer, stations, LOGGER),
            weather.PressureVisualizer(renderer, stations, LOGGER),
            rainbow.RainbowVisualizer(renderer, stations, LOGGER),
            rainbow.LightCycleVisualizer(renderer, stations, LOGGER)
        ]

        return VisualizerManager.__VISUALIZERS__

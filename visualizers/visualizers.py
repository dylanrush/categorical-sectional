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
            flight_rules.FlightRulesVisualizer(renderer, stations),
            weather.TemperatureVisualizer(renderer, stations),
            weather.PrecipitationVisualizer(renderer, stations),
            weather.PressureVisualizer(renderer, stations),
            rainbow.RainbowVisualizer(renderer, stations),
            rainbow.LightCycleVisualizer(renderer, stations)
        ]

        return VisualizerManager.__VISUALIZERS__

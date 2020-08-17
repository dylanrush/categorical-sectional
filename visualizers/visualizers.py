from lib.logger import LOGGER
from visualizers import flight_rules, rainbow, weather

VISUALIZERS = [
    flight_rules.FlightRulesVisualizer(LOGGER),
    weather.TemperatureVisualizer(LOGGER),
    rainbow.RainbowVisualizer(LOGGER),
    rainbow.LightCycleVisualizer(LOGGER)
]

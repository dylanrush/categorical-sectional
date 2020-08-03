from lib.logger import LOGGER
from visualizers import flight_rules, rainbow

VISUALIZERS = [
    flight_rules.FlightRulesVisualizer(LOGGER),
    rainbow.RainbowVisualizer(LOGGER),
    rainbow.LightCycleVisualizer(LOGGER)
]

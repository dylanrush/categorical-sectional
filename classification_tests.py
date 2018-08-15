# Free for personal use. Prohibited from commercial use without consent.
import re
import weather
from weather import VFR, MVFR, IFR, LIFR, INVALID


def get_ceiling(metar):
    """Unit tests the ceiling classification from a metar

    Arguments:
        metar {string} -- A metar report

    Returns:
        string -- Classification of the weather based on the ceiling.

      >>> get_ceiling('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      10000
      >>> get_ceiling('KRNT 132053Z 33010KT 4SM BKN041 SCT030 23/14 A3001 RMK AO2 SLP165')
      4100
      >>> get_ceiling('KRNT 132053Z 33010KT 4SM BKN041 OVC030 23/14 A3001 RMK AO2 SLP165')
      3000
      >>> get_ceiling('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165')
      3000
      >>> get_ceiling('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165')
      2500
      >>> get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165')
      900
      >>> get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165')
      900
      >>> get_ceiling('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165')
      400
      >>> get_ceiling('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165')
      400
    """

    return weather.get_ceiling(metar)

def get_ceiling_classification(metar):
    """Unit tests the ceiling classification from a metar

    Arguments:
        metar {string} -- A metar report

    Returns:
        string -- Classification of the weather based on the ceiling.

      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165'))
      'VFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 4SM SCT041 OVC030 23/14 A3001 RMK AO2 SLP165'))
      'VFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 3SM SCT041 BKN025 23/14 A3001 RMK AO2 SLP165'))
      'MVFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 BKN009 23/14 A3001 RMK AO2 SLP165'))
      'IFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 2 1/2SM SCT041 OVC009 23/14 A3001 RMK AO2 SLP165'))
      'IFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 2SM OVC004 23/14 A3001 RMK AO2 SLP165'))
      'LIFR'
      >>> get_ceiling_classification(get_ceiling('KRNT 132053Z 33010KT 2SM SCT010 OVC004 23/14 A3001 RMK AO2 SLP165'))
      'LIFR'
    """

    return weather.get_ceiling_category(metar)


def get_visibilty(metar):
    """
      Returns the amount of time in the appropriate unit.
      >>> get_visibilty('KRNT 132053Z 33010KT 10SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'VFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 4SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'MVFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 3SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'MVFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 2 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'IFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'IFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 1SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'IFR'
      >>> get_visibilty('KRNT 132053Z 33010KT 1/2SM SCT034 SCT041 23/14 A3001 RMK AO2 SLP165')
      'LIFR'
    """
    return weather.get_visibilty(metar)


if __name__ == '__main__':
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")

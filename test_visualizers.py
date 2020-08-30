from visualizers import flight_rules


def test_get_color_from_condition(
    category: str
) -> list:
    """
    From a condition, returns the color it should be rendered as, and if it should flash.

    Arguments:
        category {string} -- The weather category (VFR, IFR, et al.)

    Returns:
        [tuple] -- The color (also a tuple) and if it should blink.

    >>> test_get_color_from_condition('VFR')
    'GREEN'
    >>> test_get_color_from_condition('MVFR')
    'BLUE'
    >>> test_get_color_from_condition('IFR')
    'RED'
    >>> test_get_color_from_condition('LIFR')
    'MAGENTA'
    >>> test_get_color_from_condition('SMOKE')
    'GRAY'
    >>> test_get_color_from_condition('')
    'OFF'
    >>> test_get_color_from_condition('INOP')
    'OFF'
    >>> test_get_color_from_condition(None)
    'OFF'
    """

    return flight_rules.get_color_from_condition(category)


if __name__ == '__main__':
    import doctest

    print("Starting tests.")

    doctest.testmod()

    print("Tests finished")

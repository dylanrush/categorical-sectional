"""
Logging utilities for the WeatherMap
"""

import traceback
import inspect
from datetime import datetime, timedelta


def __get_callstack_indent_count():
    """
    Returns the number of indents that should be applied to the logging statement.

    Returns:
        int -- The numnber of indents.
    """

    try:
        cs_info = traceback.extract_stack()

        indents = len(cs_info)
        if indents < 0:
            indents = 0

        return indents
    except:
        return 0


def __get_indents(count=0):
    """
    Returns whitespace for the number of given indents.
    
    Keyword Arguments:
        count {int} -- The number of indents to return whitespace for. (default: {0})
    
    Returns:
        string -- A whitespace string.
    """

    if count < 0:
        count = 0

    return (' ' * 4) * count


def safe_log(logger, message):
    """
    Logs an INFO level message safely. Also prints it to the screen.

    Arguments:
        logger {logger} -- The logger to use.
        message {string} -- The message to log.
    """

    try:
        indents = __get_indents(__get_callstack_indent_count())
        if logger is not None:
            logger.log_info_message(indents + message)
        else:
            print('{} INFO: {}{}'.format(datetime.now(), indents, message))
    except:
        pass


def safe_log_warning(logger, message):
    """
    Logs a WARN level message safely. Also prints it to the screen.

    Arguments:
        logger {logger} -- The logger to use.
        message {string} -- The message to log.
    """

    try:
        indents = __get_indents(__get_callstack_indent_count())

        if logger is not None:
            logger.log_warning_message(indents + message)
        else:
            print('{} WARN: {}{}'.format(datetime.now(), indents, message))
    except:
        pass

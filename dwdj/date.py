import calendar
from datetime import datetime

def parse_date(datestr):
    """ Parses a date which has come from the web. Expects "%Y-%m-%d". """
    return datetime.strptime(datestr, "%Y-%m-%d")

def parse_datetime(datetimestr):
    """ Parses a date and time which has come from the web.
        Expects "%Y-%m-%d %H:%M:%S". """
    return datetime.strptime(datetimestr, "%Y-%m-%d %H:%M:%S")

def dtfromtimestamp(timestamp):
    """ Returns a datetime from timestamp ``timestamp``.

        >>> dtfromtimestamp(1234.5)
        datetime.datetime(1970, 1, 1, 0, 20, 34, 500000)
        >>> """
    return datetime.utcfromtimestamp(timestamp)

def timestampfromdt(dt):
    """ Returns a timestamp from datetime ``dt``.

        >>> timestampfromdt(datetime(1970, 1, 1, 0, 20, 34, 500000))
        1234.5
        >>> """
    return calendar.timegm(dt.timetuple()) + (dt.microsecond / 1000000.0)

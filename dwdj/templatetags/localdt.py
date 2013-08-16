from numbers import Number
from datetime import datetime

import pytz
from django import template
from django.template.defaultfilters import timesince
from django.utils import formats

def utcnow():
    # note: needed so we can override this during tests
    return datetime.utcnow()

class LocalBase(template.Node):
    def __init__(self, args):
        self.args = args

    @classmethod
    def usage(cls):
        return template.TemplateSyntaxError(
            cls.usage %(cls.tag_name, )
        )

    @classmethod
    def parse(cls, parser, token):
        args = token.split_contents()[1:]
        if len(args) < 1:
            raise cls.usage()
        return cls(args)

    def _parse(self):
        context = self.context
        in_args = list(self.args)

        if hasattr(context.get(in_args[0]), "localize"):
            tz = context[in_args.pop(0)]
        else:
            tz = context["localtz"]
        self.tz = tz

        # datetime
        self.datetime = context[in_args.pop(0)]

        # arg
        arg = None
        if in_args and in_args[0] != "as":
            arg = in_args.pop(0)
        self.arg = arg

        # output_var
        output_var = None
        if in_args:
            if len(in_args) != 2:
                raise self.usage()
            output_var = in_args[1]
        self.output_var = output_var

    def _localize_datetime(self, tz, value):
        if isinstance(value, Number):
            value = datetime.utcfromtimestamp(value)
        value_utc = value.replace(tzinfo=pytz.utc)
        return tz.normalize(value_utc.astimezone(tz))

    def _render(self):
        raise Exception("Override this!")

    def render(self, context):
        self.context = context
        self._parse()
        value = self._render()

        if self.output_var:
            context[self.output_var] = value
            return ""
        return value

class LocalDateTimeBase(LocalBase):
    """ Returns a localized datetime, date or time.

            {% local{dt,date,time} [tz] datetime [format] [as name] %}

        If ``tz`` is not specified the ``localtz`` context variable is used.

        Formatting is done by ``django.utils.formats``. """

    usage = "usage: {%% %s [tz] datetime [format] [as name] %%}"

    def _render(self):
        format = self.arg
        localized = self._localize_datetime(self.tz, self.datetime)
        return self.format_func(localized, format)


class LocalDateTime(LocalDateTimeBase):
    tag_name = "localdt"

    def format_func(self, value, format=None):
        format = format or "DATETIME_FORMAT"
        return formats.date_format(value, format)


class LocalDate(LocalDateTimeBase):
    tag_name = "localdate"
    format_func = staticmethod(formats.date_format)


class LocalTime(LocalDateTimeBase):
    tag_name = "localtime"
    format_func = staticmethod(formats.time_format)


class LocalTimesince(LocalBase):
    """ Returns a localized timesince.

            {% timesince [tz] datetime [target] [as name] %} """

    tag_name = "localtimesince"
    usage = "usage: {%% %s [tz] datetime [target] [as name] %%}"

    def _render(self):
        target = self.arg
        if target is None:
            target = utcnow()
        else:
            target = self.context[target]
        target = self._localize_datetime(self.tz, target)
        localized = self._localize_datetime(self.tz, self.datetime)
        return timesince(localized, target)


def register_all(register, values):
    for value in values:
        if hasattr(value, "tag_name"):
            register.tag(value.tag_name, value.parse)


register = template.Library()
register_all(register, globals().values())

import pytz
from datetime import datetime

from django.template import Template, Context
from nose.tools import assert_equal

from ensi_common.django.templatetags import localdt
from ensi_common.testing import parameterized

class TestLocalDateTime(object):
    test_datetime = datetime.utcfromtimestamp(1313945312.076319)
    second_datetime = datetime.utcfromtimestamp(1313950000.0)
    test_tz = pytz.timezone("Japan")

    def _render(self, template, context):
        template = Template(template)
        context = Context(context)
        return template.render(context)

    @parameterized([
        ["localdt", "Aug. 22, 2011, 1:48 a.m."],
        ["localdate", "Aug. 22, 2011"],
        ["localtime", "1:48 a.m."],
    ])
    def test_conversion(self, tag, expected):
        template = "{%% load localdt %%}{%% %s some_dt %%}" %(tag, )
        context = {
            "localtz": self.test_tz,
            "some_dt": self.test_datetime,
        }
        result = self._render(template, context)
        assert_equal(result, expected)

    @parameterized([
        ["{% localtime other_tz some_dt %}", "6:48 p.m."],
        ["{% localtime other_tz some_dt as foo %}a{{ foo }}b", "a6:48 p.m.b"],
        ["{% localtime some_dt as foo %}a{{ foo }}b", "a1:48 a.m.b"],
        ["{% localtimesince some_dt %}", "1 hour, 18 minutes"],
        ["{% localtimesince other_tz some_dt %}", "1 hour, 18 minutes"],
        ["{% localtimesince other_tz some_dt other_dt %}", "4 hours, 4 minutes"],
        ["{% localtimesince some_dt as foo %}a{{ foo }}b", "a1 hour, 18 minutesb"],
        ["{% localtimesince other_tz some_dt as foo %}a{{ foo }}b", "a1 hour, 18 minutesb"],
        ["{% localtimesince other_tz some_dt other_dt as foo %}a{{ foo }}b", "a4 hours, 4 minutesb"],
    ])
    def test_parsing(self, input, expected):
        oldutcnow = localdt.utcnow
        localdt.utcnow = lambda: self.second_datetime
        try:
            template = "{% load localdt %}" + input
            context = {
                "localtz": self.test_tz,
                "other_tz": pytz.timezone("Africa/Johannesburg"),
                "some_dt": self.test_datetime,
                "other_dt": datetime.utcfromtimestamp(1313960000.0)
            }
            result = self._render(template, context)
            assert_equal(result, expected)
        finally:
            localdt.utcnow = oldutcnow

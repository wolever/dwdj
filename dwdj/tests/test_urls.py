from mock import Mock
from nose.tools import assert_equal

from ensi_common.testing import parameterized

from ..urls import include_factory


dummy = object()

class TestIncludeFactory(object):
    tests = [
        ("foo", "foo"),
        (".foo", "p.k.g.foo"),
        ("..foo", "p.k.foo"),
        (dummy, dummy),
    ]

    @parameterized(tests)
    def test_include_factory(self, input, expected):
        m = Mock()
        include = include_factory("p.k.g", includefunc=m)
        include(input)

        assert_equal(m.call_args, ((expected, ), {}))

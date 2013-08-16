import time
import random

from django.forms import widgets
from django.db import models as m

from .strutil import to36


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], ["^fi\.dj\.fields\.IDField"])


class IDField(m.Field):
    """ An ID field which is a 12 byte string, which is a base36 encoded 62
        bit integer, where the leading bits are time, and the trailing bits
        are random. """
    description = "A unique ID 12 byte string, suitable for use as a unique ID"
    max_length = 12

    # Note: because of http://code.djangoproject.com/ticket/13696, IDField will
    # do Bad Things when it's used with an inline admin.

    @classmethod
    def new(cls):
        """ Returns a unique 62 bit ID which is based on a random number and
            the current time. """
        # Truncate the current unix time to 30 bits...
        curtime = int(time.time()) & ((1<<30)-1)
        # ... then slap some random bits on the end.
        # Do this to help the database maintain temporal locality.
        # (it's possible that these should be swapped - with the
        # random bits coming first and the time bits coming second)
        return to36((curtime << 32) | random.getrandbits(32))

    def __init__(self, primary_key=True, auto=True, **kwargs):
        self.auto = auto
        super(IDField, self).__init__(primary_key=primary_key,
                                      default=None,
                                      max_length=self.max_length,
                                      blank=True)

    def db_type(self, connection):
        return "CHAR(%s)" %(self.max_length, )

    def to_python(self, value):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, (int, long)):
            return to36(value)
        elif value is None:
            # When an object is being deleted, its primary key is null'd
            return value
        raise TypeError("Bad ID Field value: %r (bad type)" %(value, ))

    def pre_save(self, model_instance, add):
        # Note: only set on save because Django's admin (or possibly just the
        # 'TabularInline' admin) gets upset when the primary key changes (as it
        # would if a 'default' value was set (eg, 'default=self.new').
        cur_val = super(IDField, self).pre_save(model_instance, add)
        if not cur_val and self.auto:
            cur_val = self.new()
            setattr(model_instance, self.attname, cur_val)
        if cur_val and len(cur_val) > self.max_length:
            raise ValueError("invalid %r on %r: %r is longer than %r"
                             %(self.attname, model_instance, cur_val,
                               self.max_length))
        return cur_val

    def get_prep_value(self, value):
        if isinstance(value, (int, long)):
            # This can happen when using 'dumpdata', for some reason
            return to36(value)
        return value

    def formfield(self, **kwargs):
        defaults = {'widget': ReadOnlyWidget}
        defaults.update(kwargs)
        return super(IDField, self).formfield(**defaults)


class ReadOnlyWidget(widgets.Widget):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='hidden', name=name)
        if value != '':
            final_attrs['value'] = widgets.force_text(value)
        return widgets.format_html('<input{0} />{1}',
                                   widgets.flatatt(final_attrs),
                                   value)

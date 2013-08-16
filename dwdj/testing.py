import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from nose.tools import assert_equal

def assert_redirects(resp, url, status=(301, 302)):
    assert resp.status_code in status or resp.status_code == status, \
        "response status %r not valid (not %s)" %(resp.status, status)
    assert_equal(resp.get("Location", "<no location header>"),
                 "http://testserver" + url)

def loggedin_client(username="admin"):
    c = Client()
    result = c.login(username=username, password="asdf")
    assert result, "login failed"
    return c

def get_ok(c, *args, **kwargs):
    resp = c.get(*args, **kwargs)
    if resp.status_code != 200:
        raise AssertionError("unexpected status code: %r; headers:\n%s"
                             %(resp.status_code,
                               "\n".join("%s: %s" %x for x in resp.items())))

    return resp


class APITestCase(TestCase):
    def url(self, name, *args, **kwargs):
        return reverse(name, args=args, kwargs=kwargs, current_app="api")

    def login(self, username="admin", password="asdf"):
        login_result = self.client.login(username=username,
                                         password=password)
        assert login_result, "login failed"

    def call(self, method, url, *args, **kwargs):
        return getattr(self.client, method)("/api/" + url, {
            "__kwargs": json.dumps(kwargs),
            "__args": json.dumps(args),
        })

    def resp_data(self, resp):
        try:
            resp_obj = json.loads(resp.content)
        except ValueError:
            print "error decoding json:"
            print resp.content
            raise
        assert resp_obj["ok"], "response returned error: %r" %(resp_obj, )
        print resp_obj
        return resp_obj["data"]

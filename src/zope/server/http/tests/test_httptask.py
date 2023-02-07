"""
Tests for httptask.py.

"""
import unittest

from zope.server.http import httptask
from zope.server.http.httprequestparser import HTTPRequestParser


class MockRequestData(HTTPRequestParser):

    def __init__(self):
        HTTPRequestParser.__init__(self, None)


class MockChannel:

    server = property(lambda s: s)
    SERVER_IDENT = 'server_ident'
    port = 0
    server_name = 'localhost'
    creation_time = 0
    addr = (server_name, port)

    flush_called = False

    def flush(self):
        self.flush_called = True


class TestHTTPTask(unittest.TestCase):

    def _makeOne(self, channel=None, data=None):
        return httptask.HTTPTask(channel or MockChannel(),
                                 data or MockRequestData())

    def test_version_fallback(self):
        data = MockRequestData()
        data.version = '2.0'

        task = self._makeOne(data=data)
        self.assertEqual(task.version, '1.0')

    def test_setResponseHeaders(self):
        task = self._makeOne()
        self.assertEqual({}, task.response_headers)

        task.setResponseHeaders({'key': 42})
        self.assertEqual({'key': 42}, task.response_headers)

        # And they accumulate
        task.setResponseHeaders({'key': 1, 'color': 'green'})
        self.assertEqual({'key': 1, 'color': 'green'},
                         task.response_headers)

    def test_setAuthUserName(self):
        task = self._makeOne()
        task.setAuthUserName('joe')
        self.assertEqual(task.auth_user_name, 'joe')

    def test_prepareResponseHeaders_unknown_version(self):
        # For this to happen, someone external would have to
        # manually set version; our constructor caps it
        # to a known value.
        task = self._makeOne()
        task.close_on_finish = False

        task.version = '2.0'
        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 1)

    def test_prepareResponseHeaders_10_keep_alive_no_length(self):
        task = self._makeOne()
        self.assertEqual(task.version, '1.0')
        task.close_on_finish = False

        task.request_data.headers['CONNECTION'] = 'keep-alive'

        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 1)

    def test_prepareResponseHeaders_11_connection_close_response_header(self):
        task = self._makeOne()
        self.assertEqual(task.version, '1.0')
        task.version = '1.1'
        task.close_on_finish = False

        task.appendResponseHeaders(['connection: close'])

        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 1)

    def test_prepareResponseHeaders_11_transfer_encoding(self):
        task = self._makeOne()
        self.assertEqual(task.version, '1.0')
        task.version = '1.1'
        task.close_on_finish = False

        task.setResponseHeaders({'Transfer-Encoding': 'identity'})

        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 1)

        # But chunked encoding is special cased to not close it.
        task.close_on_finish = False

        task.setResponseHeaders({'Transfer-Encoding': 'chunked'})

        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 0)

    def test_prepareResponseHeaders_11_304(self):
        task = self._makeOne()
        task.version = '1.1'
        task.close_on_finish = True

        task.setResponseStatus('304', 'Headers')

        task.prepareResponseHeaders()

        self.assertEqual(task.close_on_finish, 0)

    def test_getCGIEnvironment_cached(self):
        task = self._makeOne()
        task.request_data.path = '/'
        env = task.getCGIEnvironment()

        self.assertIs(env, task.getCGIEnvironment())

    def test_getCGIEnvironment_resolver(self):
        task = self._makeOne()
        task.request_data.path = '/'

        class Resolver:
            cache = {
                MockChannel.addr[0]: (None, None, 'RemoteHost')
            }

        task.channel.resolver = Resolver()

        env = task.getCGIEnvironment()

        self.assertEqual(env['REMOTE_HOST'], 'RemoteHost')

    def test_flush(self):
        task = self._makeOne()

        task.flush()

        self.assertTrue(task.channel.flush_called)

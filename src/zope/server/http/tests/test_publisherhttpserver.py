"""Tests for publisherhttpserver.py"""

import unittest

from zope.server.http import publisherhttpserver


class TestPMDBHTTPServer(unittest.TestCase):

    def test_application_calls_debugger(self):
        from zope.server.http import wsgihttpserver
        pm_called = []

        def post_mortem(exc_info):
            pm_called.append(True)
            raise exc_info[1]

        class PublishException(Exception):
            pass

        def publish(*args, **kwargs):
            self.assertFalse(kwargs.get('handle_errors', True))
            raise PublishException()

        orig_post = wsgihttpserver.PMDBWSGIHTTPServer.post_mortem
        orig_publish = publisherhttpserver._publish

        wsgihttpserver.PMDBWSGIHTTPServer.post_mortem = staticmethod(
            post_mortem)
        publisherhttpserver._publish = publish

        class Request:
            def __init__(self, *args):
                pass

        try:
            app = publisherhttpserver.PMDBHTTPServer._make_application(Request)
            with self.assertRaises(PublishException):
                app({'wsgi.input': None}, None)
        finally:
            wsgihttpserver.PMDBWSGIHTTPServer.post_mortem = orig_post
            publisherhttpserver._publish = orig_publish

        self.assertTrue(pm_called)


class TestPublisherHTTPServer(unittest.TestCase):

    def test_application(self):
        class Request:
            def __init__(self, *args):
                self.response = self
                self.publication = self

            def close(self, *args, **kwargs):
                pass

            internalError = endRequest = handleException = close

            def getStatusString(self):
                return "STATUS"

            def getHeaders(self):
                return []

            def consumeBody(self):
                return 'BODY'

        server = publisherhttpserver.PublisherHTTPServer(
            ip='127.0.0.1', port=0, request_factory=Request)
        self.addCleanup(server.close)
        application = server.application

        def start(status, headers):
            self.assertEqual(status, 'STATUS')
            self.assertEqual(headers, [])
        result = application({'wsgi.input': None}, start)
        self.assertEqual(result, 'BODY')

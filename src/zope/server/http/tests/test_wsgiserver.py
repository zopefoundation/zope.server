##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""Test Publisher-based HTTP Server
"""

import sys
import unittest
import warnings
from contextlib import closing
from contextlib import contextmanager
from http.client import HTTPConnection
from io import BytesIO
from io import StringIO

import paste.lint
import zope.component
from zope.component.testing import PlacelessSetup
from zope.i18n.interfaces import IUserPreferredCharsets
from zope.publisher.base import DefaultPublication
from zope.publisher.browser import BrowserRequest
from zope.publisher.http import HTTPCharsets
from zope.publisher.http import HTTPRequest
from zope.publisher.http import IHTTPRequest
from zope.publisher.interfaces import Redirect
from zope.publisher.interfaces import Retry
from zope.publisher.publish import publish

from zope.server.tests import LoopTestMixin
from zope.server.tests.asyncerror import AsyncoreErrorHookMixin


HTTPRequest.STAGGER_RETRIES = 0  # Don't pause.

# By using io.BytesIO() instead of cStringIO.StringIO() on Python 2 we make
# sure we're not trying to accidentally print unicode to stdout/stderr.
NativeStringIO = BytesIO if str is bytes else StringIO


@contextmanager
def capture_output(stdout=None, stderr=None):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout = stdout or NativeStringIO()
    sys.stderr = stderr = stderr or NativeStringIO()
    try:
        yield stdout, stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class Conflict(Exception):
    """
    Pseudo ZODB conflict error.
    """


ERROR_RESPONSE = b"error occurred"
RESPONSE = b"normal response"


class DummyException(Exception):
    value = "Dummy Exception to test start_response"

    def __str__(self):
        return repr(self.value)


class PublicationWithConflict(DefaultPublication):

    def handleException(self, object, request, exc_info, retry_allowed=1):
        if exc_info[0] is Conflict and retry_allowed:
            # This simulates a ZODB retry.
            raise Retry(exc_info)
        else:
            DefaultPublication.handleException(self, object, request, exc_info,
                                               retry_allowed)


class Accepted(Exception):
    pass


class tested_object:
    """Docstring required by publisher."""
    tries = 0

    def __call__(self, REQUEST):
        return 'URL invoked: %s' % REQUEST.URL

    def redirect_method(self, REQUEST):
        """Generate a redirect using the redirect() method."""
        REQUEST.response.redirect("/redirect")

    def redirect_exception(self):
        """Generate a redirect using an exception."""
        raise Redirect("/exception")

    def conflict(self, REQUEST, wait_tries):
        """Return 202 status only after (wait_tries) tries."""
        if self.tries >= int(wait_tries):
            raise Accepted
        else:
            self.tries += 1
            raise Conflict

    def proxy(self, REQUEST):
        """Behave like a real proxy response."""
        REQUEST.response.addHeader('Server', 'Fake/1.0')
        REQUEST.response.addHeader('Date', 'Thu, 01 Apr 2010 12:00:00 GMT')
        return 'Proxied Content'


class WSGIInfo:
    """Docstring required by publisher"""

    def __call__(self, REQUEST):
        """Return a list of variables beginning with 'wsgi.'"""
        r = []
        for name in REQUEST.keys():
            if name.startswith('wsgi.'):
                r.append(name)
        return ' '.join(r)

    def version(self, REQUEST):
        """Return WSGI version"""
        return str(REQUEST['wsgi.version'])

    def url_scheme(self, REQUEST):
        """Return WSGI URL scheme"""
        return REQUEST['wsgi.url_scheme']

    def multithread(self, REQUEST):
        """Return WSGI multithreadedness"""
        return str(bool(REQUEST['wsgi.multithread']))

    def multiprocess(self, REQUEST):
        """Return WSGI multiprocessedness"""
        return str(bool(REQUEST['wsgi.multiprocess']))

    def run_once(self, REQUEST):
        """Return whether WSGI app is invoked only once or not"""
        return str(bool(REQUEST['wsgi.run_once']))

    def proxy_scheme(self, REQUEST):
        """Return the proxy scheme."""
        return REQUEST['zserver.proxy.scheme']

    def proxy_host(self, REQUEST):
        """Return the proxy host."""
        return REQUEST['zserver.proxy.host']


class Tests(LoopTestMixin,
            AsyncoreErrorHookMixin,
            PlacelessSetup,
            unittest.TestCase):

    thread_name = 'test_wsgiserver'

    def _getServerClass(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.http.wsgihttpserver import WSGIHTTPServer
        return WSGIHTTPServer

    def setUp(self):
        super().setUp()
        zope.component.provideAdapter(HTTPCharsets, [IHTTPRequest],
                                      IUserPreferredCharsets, '')

    def _makeServer(self):
        obj = tested_object()
        obj.folder = tested_object()
        obj.folder.item = tested_object()
        obj._protected = tested_object()
        obj.wsgi = WSGIInfo()

        pub = PublicationWithConflict(obj)

        def application(environ, start_response):
            request = BrowserRequest(environ['wsgi.input'], environ)
            request.setPublication(pub)
            request = publish(request)
            response = request.response
            start_response(response.getStatusString(), response.getHeaders())
            return response.consumeBodyIter()

        ServerClass = self._getServerClass()
        self.server = ServerClass(
            application,
            'Browser',
            self.LOCALHOST,
            self.CONNECT_TO_PORT,
            task_dispatcher=self.td)
        return self.server

    def invokeRequest(self, path='/',
                      return_response=False):
        with closing(HTTPConnection(self.LOCALHOST, self.port)) as h:
            h.putrequest('GET', path)
            h.putheader('Accept', 'text/plain')
            h.endheaders()
            response = h.getresponse()
            length = int(response.getheader('Content-Length', '0'))
            if length:
                response_body = response.read(length)
            else:
                response_body = b''

            self.assertEqual(length, len(response_body))

            if return_response:
                return response, response_body
            else:
                return response.status, response_body

    def testDeeperPath(self):
        status, response_body = self.invokeRequest('/folder/item')
        self.assertEqual(status, 200)
        expect_response = 'URL invoked: http://%s:%d/folder/item' % (
            self.LOCALHOST, self.port)
        self.assertEqual(response_body, expect_response.encode('ascii'))

    def testNotFound(self):
        status, _response_body = self.invokeRequest('/foo/bar')
        self.assertEqual(status, 404)

    def testUnauthorized(self):
        status, _response_body = self.invokeRequest('/_protected')
        self.assertEqual(status, 401)

    def testRedirectMethod(self):
        status, _response_body = self.invokeRequest('/redirect_method')
        self.assertEqual(status, 303)

    def testRedirectException(self):
        status, _response_body = self.invokeRequest('/redirect_exception')
        self.assertEqual(status, 303)
        status, _response_body = self.invokeRequest(
            '/folder/redirect_exception')
        self.assertEqual(status, 303)

    def testConflictRetry(self):
        status, _response_body = self.invokeRequest('/conflict?wait_tries=2')
        # Expect the "Accepted" response since the retries will succeed.
        self.assertEqual(status, 202)

    def testFailedConflictRetry(self):
        status, _response_body = self.invokeRequest('/conflict?wait_tries=10')
        # Expect a "Conflict" response since there will be too many
        # conflicts.
        self.assertEqual(status, 409)

    def testServerAsProxy(self):
        response, response_body = self.invokeRequest(
            '/proxy', return_response=True)
        # The headers set by the proxy are honored,
        self.assertEqual(
            response.getheader('Server'), 'Fake/1.0')
        self.assertEqual(
            response.getheader('Date'), 'Thu, 01 Apr 2010 12:00:00 GMT')
        # The server adds a Via header.
        self.assertEqual(
            response.getheader('Via'), 'zope.server.http (Browser)')
        # And the content got here too.
        self.assertEqual(response_body, b'Proxied Content')

    def testWSGIVariables(self):
        # Assert that the environment contains all required WSGI variables
        _status, response_body = self.invokeRequest('/wsgi')
        wsgi_variables = set(response_body.decode('ascii').split())
        self.assertEqual(wsgi_variables,
                         {'wsgi.version', 'wsgi.url_scheme', 'wsgi.input',
                          'wsgi.errors', 'wsgi.multithread',
                          'wsgi.multiprocess', 'wsgi.run_once'})

    def testWSGIVersion(self):
        _status, response_body = self.invokeRequest('/wsgi/version')
        self.assertEqual(b"(1, 0)", response_body)

    def testWSGIURLScheme(self):
        _status, response_body = self.invokeRequest('/wsgi/url_scheme')
        self.assertEqual(b'http', response_body)

    def testWSGIMultithread(self):
        _status, response_body = self.invokeRequest('/wsgi/multithread')
        self.assertEqual(b'True', response_body)

    def testWSGIMultiprocess(self):
        _status, response_body = self.invokeRequest('/wsgi/multiprocess')
        self.assertEqual(b'True', response_body)

    def testWSGIRunOnce(self):
        _status, response_body = self.invokeRequest('/wsgi/run_once')
        self.assertEqual(b'False', response_body)

    def testWSGIProxy(self):
        _status, response_body = self.invokeRequest(
            'https://zope.org:8080/wsgi/proxy_scheme')
        self.assertEqual(b'https', response_body)
        _status, response_body = self.invokeRequest(
            'https://zope.org:8080/wsgi/proxy_host')
        self.assertEqual(b'zope.org:8080', response_body)

    def test_ensure_multiple_task_write_calls(self):
        # In order to get data out as fast as possible, the WSGI server needs
        # to call task.write() multiple times.
        orig_app = self.server.application

        def app(eviron, start_response):
            start_response('200 Ok', [])
            return [b'This', b'is', b'my', b'response.']
        self.server.application = app

        class FakeTask:
            wrote_header = 0
            counter = 0

            def getCGIEnvironment(self):
                return {}

            class request_data:
                def getBodyStream(self):
                    return BytesIO()

            request_data = request_data()
            setResponseStatus = appendResponseHeaders = lambda *_: None

            def wroteResponseHeader(self):
                return self.wrote_header

            def write(self, v):
                self.counter += 1

        task = FakeTask()
        self.server.executeRequest(task)
        self.assertEqual(task.counter, 4)

        self.server.application = orig_app

    def _getFakeAppAndTask(self):

        def app(environ, start_response):
            try:
                raise DummyException()
            except DummyException:
                start_response(
                    '500 Internal Error',
                    [('Content-type', 'text/plain')],
                    sys.exc_info())
                return ERROR_RESPONSE.split()
            raise AssertionError("Can never get here")

        class FakeTask:
            wrote_header = 0
            status = None
            reason = None
            response = []
            accumulated_headers = None

            def __init__(self):
                self.accumulated_headers = []
                self.response_headers = {}

            def getCGIEnvironment(self):
                return {}

            class request_data:

                def getBodyStream(self):
                    return BytesIO()

            request_data = request_data()

            def appendResponseHeaders(self, lst):
                accum = self.accumulated_headers
                if accum is None:
                    self.accumulated_headers = accum = []
                accum.extend(lst)

            def setResponseStatus(self, status, reason):
                self.status = status
                self.reason = reason

            def wroteResponseHeader(self):
                return self.wrote_header

            def write(self, v):
                self.response.append(v)

        return app, FakeTask()

    def test_start_response_with_no_headers_sent(self):
        # start_response exc_info if no headers have been sent
        orig_app = self.server.application
        self.server.application, task = self._getFakeAppAndTask()
        task.accumulated_headers = ['header1', 'header2']
        task.accumulated_headers = {'key1': 'value1', 'key2': 'value2'}

        self.server.executeRequest(task)

        self.assertEqual(task.status, "500")
        self.assertEqual(task.response, ERROR_RESPONSE.split())
        # any headers written before are cleared and
        # only the most recent one is added.
        self.assertEqual(task.accumulated_headers,
                         ['Content-type: text/plain'])
        # response headers are cleared. They'll be rebuilt from
        # accumulated_headers in the prepareResponseHeaders method
        self.assertEqual(task.response_headers, {})

        self.server.application = orig_app

    def test_multiple_start_response_calls(self):
        # if start_response is called more than once with no exc_info
        _ignore, task = self._getFakeAppAndTask()
        task.wrote_header = 1

        self.assertRaises(AssertionError, self.server.executeRequest, task)

    def test_start_response_with_headers_sent(self):
        # If headers have been sent it raises the exception
        orig_app = self.server.application
        self.server.application, task = self._getFakeAppAndTask()

        # If headers have already been written an exception is raised
        task.wrote_header = 1
        self.assertRaises(DummyException, self.server.executeRequest, task)

        self.server.application = orig_app

    def test_closes_iterator(self):
        """PEP-0333 specifies that if an iterable returned by
           a WSGI application has a 'close' method, it must
           be called.

           paste.lint has this check as well, but it writes a
           message to stderr instead of raising an error or
           issuing a warning.
        """
        orig_app = self.server.application
        app, _ = self._getFakeAppAndTask()

        class CloseableIterator:

            closed = False

            def __init__(self, value):
                self._iter = iter(value)
                self.value = value

            def __iter__(self):
                return self

            def __next__(self):
                return next(self._iter)
            next = __next__

            def close(self):
                self.closed = True

        iterator = CloseableIterator([b"Klaatu", b"barada", b"nikto"])

        def app(environ, start_response):
            start_response("200 Ok", [], None)
            return iterator

        self.server.application = app
        self.invokeRequest("/")
        self.assertTrue(iterator.closed,
                        "close method wasn't called on iterable")

        self.server.application = orig_app

    def test_wsgi_compliance(self):
        orig_app = self.server.application
        self.server.application = paste.lint.middleware(orig_app)

        with warnings.catch_warnings(record=True) as w:
            self.invokeRequest("/foo")
        self.assertEqual(len(w), 0, [str(m) for m in w])
        self.server.application = orig_app


class TestWSGIHttpServer(unittest.TestCase):

    def test_secure_environment(self):
        from zope.server.http.wsgihttpserver import WSGIHTTPServer

        class Task:
            def __init__(self, env):
                self.env = env
                self.request_data = self

            def getCGIEnvironment(self):
                return self.env

            def getBodyStream(self):
                return None

        env = WSGIHTTPServer._constructWSGIEnvironment(Task({}))
        self.assertEqual("http", env['wsgi.url_scheme'])

        env = WSGIHTTPServer._constructWSGIEnvironment(Task({'HTTPS': 'on'}))
        self.assertEqual("https", env['wsgi.url_scheme'])

        env = WSGIHTTPServer._constructWSGIEnvironment(
            Task({'SERVER_PORT_SECURE': "1"}))
        self.assertEqual("https", env['wsgi.url_scheme'])


class PMDBTests(Tests):

    def _getServerClass(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.http.wsgihttpserver import PMDBWSGIHTTPServer
        return PMDBWSGIHTTPServer

    def testWSGIVariables(self):
        # Assert that the environment contains all required WSGI variables
        _status, response_body = self.invokeRequest('/wsgi')
        wsgi_variables = set(response_body.decode('ascii').split())
        self.assertEqual(wsgi_variables,
                         {'wsgi.version', 'wsgi.url_scheme', 'wsgi.input',
                          'wsgi.errors', 'wsgi.multithread',
                          'wsgi.multiprocess', 'wsgi.handleErrors',
                          'wsgi.run_once'})

    def test_multiple_start_response_calls(self):
        # if start_response is called more than once with no exc_info
        _ignore, task = self._getFakeAppAndTask()
        task.wrote_header = 1

        # monkey-patch pdb.post_mortem so we don't go into pdb session.
        pm_traceback = []

        def fake_post_mortem(tb):
            import traceback
            pm_traceback.extend(traceback.format_tb(tb))

        import pdb
        orig_post_mortem = pdb.post_mortem
        pdb.post_mortem = fake_post_mortem

        with capture_output():
            self.assertRaises(AssertionError, self.server.executeRequest, task)
        expected_msg = "start_response called a second time"
        self.assertTrue(expected_msg in pm_traceback[-1])
        pdb.post_mortem = orig_post_mortem

    def test_start_response_with_headers_sent(self):
        # If headers have been sent it raises the exception, which will
        # be caught by the server and invoke pdb.post_mortem.
        orig_app = self.server.application
        self.server.application, task = self._getFakeAppAndTask()
        task.wrote_header = 1

        # monkey-patch pdb.post_mortem so we don't go into pdb session.
        pm_traceback = []

        def fake_post_mortem(tb):
            import traceback
            pm_traceback.extend(traceback.format_tb(tb))

        import pdb
        orig_post_mortem = pdb.post_mortem
        pdb.post_mortem = fake_post_mortem

        with capture_output():
            self.assertRaises(DummyException, self.server.executeRequest, task)
        self.assertTrue("raise DummyException" in pm_traceback[-1])

        self.server.application = orig_app
        pdb.post_mortem = orig_post_mortem


class TestPaste(unittest.TestCase):

    def test_run_paste(self):
        from zope.server.http.wsgihttpserver import run_paste
        with self.assertRaises(OverflowError):
            run_paste(None, {}, threads=0, port=-5)

    def test_run_paste_loop(self):
        from zope.server.http import wsgihttpserver

        class Server:
            def __init__(self, *args, **kwargs):
                pass

            def close(self):
                pass

        class asyncore:
            looped = False

            def loop(self):
                self.looped = True

        orig_wsgi = wsgihttpserver.WSGIHTTPServer
        orig_async = wsgihttpserver.asyncore

        wsgihttpserver.WSGIHTTPServer = Server
        a = wsgihttpserver.asyncore = asyncore()

        try:
            wsgihttpserver.run_paste(None, None, threads=0)
        finally:
            wsgihttpserver.WSGIHTTPServer = orig_wsgi
            wsgihttpserver.asyncore = orig_async

        self.assertTrue(a.looped)

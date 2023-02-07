"""Tests for trigger.py"""

import sys
import unittest

from zope.server import trigger


class TestFunctions(unittest.TestCase):

    def test_positive_id(self):
        expected = 18446744073709551574 if sys.maxsize > 2**32 else 4294967254
        trigger.id = lambda o: -42
        try:
            self.assertEqual(trigger.positive_id(None), expected)
        finally:
            del trigger.id


@unittest.skipIf(not hasattr(trigger, 'pipetrigger'),
                 "pipetrigger not available on Windows")
class TestPipeTrigger(unittest.TestCase):

    def _getFUT(self):
        return trigger.pipetrigger

    def _makeOne(self):
        t = self._getFUT()()
        self.addCleanup(t.close)
        return t

    def test_repr(self):
        t = self._makeOne()
        self.assertIn(self._getFUT().kind, repr(t))

    def test_handle_connect(self):
        t = self._makeOne()
        t.handle_connect()

    def test_handle_close(self):
        t = self._makeOne()
        t.handle_close()

    def test_handle_read_error(self):
        t = self._makeOne()
        t.close()

        def recv(_s):
            raise OSError
        t.recv = recv

        def thunk():
            raise AssertionError("I should not be called")
        t.thunks.append(thunk)
        t.handle_read()

    def test_thunk_error(self):
        import io
        buf = io.BytesIO() if bytes is str else io.StringIO()

        def thunk():
            raise Exception("TestException")
        t = self._makeOne()
        t.recv = lambda s: ''
        t.thunks.append(thunk)
        trigger.print = buf.write
        try:
            t.handle_read()
        finally:
            del trigger.print

        self.assertIn('TestException', buf.getvalue())

    def test_pull(self):
        t = self._makeOne()
        t.pull_trigger()
        # The side effects of this are hard to test


class TestSocketTrigger(TestPipeTrigger):

    def _getFUT(self):
        return trigger.sockettrigger

    def test_connect_failure_retry(self):

        class T(self._getFUT()):
            def _connect_client(self, w, connect_address):
                import errno
                raise OSError(errno.EADDRINUSE)

        with self.assertRaises(trigger.BindError):
            T()

    def test_connect_failure_no_retry(self):
        import socket

        class T(self._getFUT()):
            def _connect_client(self, w, connect_address):
                raise OSError("Nope")

        with self.assertRaises(socket.error):
            T()

# -*- coding: utf-8 -*-
"""
Tests for trigger.py

"""
from __future__ import print_function
import unittest

from zope.server import trigger

class TestFunctions(unittest.TestCase):

    def test_positive_id(self):

        trigger.id = lambda o: -42
        try:
            # This is possibly only correct on 64-bit platforms
            self.assertEqual(18446744073709551574,
                             trigger.positive_id(None))
        finally:
            del trigger.id

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
            import socket
            raise socket.error
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
        t.close()
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
                import socket
                import errno
                raise socket.error(errno.EADDRINUSE)

        with self.assertRaises(trigger.BindError):
            T()

    def test_connect_failure_no_retry(self):
        import socket

        class T(self._getFUT()):
            def _connect_client(self, w, connect_address):
                raise socket.error("Nope")

        with self.assertRaises(socket.error):
            T()

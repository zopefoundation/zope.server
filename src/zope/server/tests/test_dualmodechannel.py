# -*- coding: utf-8 -*-
"""
Tests for dualmodechannel.py.

"""
import unittest

from zope.server.dualmodechannel import DualModeChannel

class TestDualModeChannel(unittest.TestCase):

    def test_handle_write_non_async(self):
        channel = DualModeChannel(None, None)

        channel.set_sync()
        # Does nothing, no side effects
        channel.handle_write()

    def test_handle_read_non_async(self):
        channel = DualModeChannel(None, None)

        channel.set_sync()
        # Does nothing, no side effects
        channel.handle_read()

    def test_handle_read_will_close(self):
        channel = DualModeChannel(None, None)

        channel.close_when_done()
        # Does nothing, no side effects
        channel.handle_read()

    def test_handle_write_flush_error(self):
        import socket
        class C(DualModeChannel):
            error_called = False
            def __init__(self):
                DualModeChannel.__init__(self, None, None)

            def _flush_some(self):
                raise socket.error()

            def handle_error(self):
                self.error_called = True

        channel = C()
        channel.outbuf.append(b'data')
        channel.handle_write()
        self.assertTrue(channel.error_called)


    def test_handle_read_recv_error(self):
        import socket
        class C(DualModeChannel):
            error_called = False
            def __init__(self):
                DualModeChannel.__init__(self, None, None)

            def recv(self, _count):
                raise socket.error()

            def handle_error(self):
                self.error_called = True

        channel = C()
        channel.handle_read()
        self.assertTrue(channel.error_called)

    def test_write_flushes(self):
        class C(DualModeChannel):
            flush_called = False
            def _flush_some(self):
                self.flush_called = True
                return False

        class A(object):
            send_bytes = 1
            outbuf_overflow = 100

        channel = C(None, None, A())
        channel.write(b'some bytes')
        self.assertTrue(channel.flush_called)

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
        class C(DualModeChannel):
            error_called = False

            def __init__(self):
                DualModeChannel.__init__(self, None, None)

            def _flush_some(self):
                raise OSError()

            def handle_error(self):
                self.error_called = True

        channel = C()
        channel.outbuf.append(b'data')
        channel.handle_write()
        self.assertTrue(channel.error_called)

    def test_handle_read_recv_error(self):
        class C(DualModeChannel):
            error_called = False

            def __init__(self):
                DualModeChannel.__init__(self, None, None)

            def recv(self, _count):
                raise OSError()

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

        class A:
            send_bytes = 1
            outbuf_overflow = 100

        channel = C(None, None, A())
        channel.write(b'some bytes')
        self.assertTrue(channel.flush_called)

    def test_channels_accept_iterables(self):
        # Channels accept iterables (they special-case strings).

        from zope.server.tests.test_serverbase import FakeSocket
        socket = FakeSocket()
        channel = DualModeChannel(socket, ('localhost', 42))

        written = channel.write(b"First")
        self.assertEqual(5, written)

        channel.flush()
        self.assertEqual(socket.data.decode('ascii'),
                         'First')

        written = channel.write([b"\n", b"Second", b"\n", b"Third"])
        self.assertEqual(13, written)

        channel.flush()
        self.assertEqual(socket.data.decode('ascii'),
                         "First\n"
                         "Second\n"
                         "Third")

        def count():
            yield b'\n1\n2\n3\n'
            yield b'I love to count. Ha ha ha.'

        written = channel.write(count())
        self.assertEqual(written, 33)

        channel.flush()
        self.assertEqual(socket.data.decode('ascii'),
                         "First\n"
                         "Second\n"
                         "Third\n"
                         "1\n"
                         "2\n"
                         "3\n"
                         "I love to count. Ha ha ha.")

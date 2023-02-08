"""
Tests for task.py

"""
import unittest

from zope.server.task import AbstractTask


class MockChannel:

    log_socket_errors = False
    closing_when_done = False
    hit_log = None

    adj = server = property(lambda s: s)

    def close_when_done(self):
        self.closing_when_done = True


class TestAbstractTask(unittest.TestCase):

    def test_socket_error(self):
        import socket

        class T(AbstractTask):
            def _do_service(self):
                raise OSError()

        t = T(MockChannel())
        t.service()
        self.assertTrue(t.close_on_finish)
        self.assertTrue(t.channel.closing_when_done)

        t.channel.log_socket_errors = True
        with self.assertRaises(socket.error):
            t.service()

    def test_arbitrary_error(self):

        class E(Exception):
            pass

        class T(AbstractTask):
            def _do_service(self):
                raise E()

        t = T(MockChannel())
        with self.assertRaises(E):
            t.service()

        t.channel.exception = lambda: None
        t.service()

    def test_hit_log(self):
        class Log:
            called = False

            def log(self, _task):
                self.called = True

        class T(AbstractTask):
            def _do_service(self):
                pass

        t = T(MockChannel())
        t.channel.hit_log = Log()
        t.service()
        self.assertTrue(t.channel.hit_log.called)

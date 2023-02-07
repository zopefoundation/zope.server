"""
Tests for serverchannelbase.py

"""
import unittest

from zope.testing.cleanup import CleanUp

from zope.server import serverchannelbase


class TestServerChannelBase(CleanUp,
                            unittest.TestCase):

    def _makeOne(self):
        return serverchannelbase.ServerChannelBase(None, None, None)

    def test_add_del_channel(self):
        channel = self._makeOne()
        channel.add_channel()
        self.assertEqual(channel.active_channels, {None: channel})
        channel.del_channel()
        self.assertEqual(channel.active_channels, {})

    def test_handle_comm_err_logging(self):
        from zope.server.adjustments import Adjustments
        adj = Adjustments()
        adj.log_socket_errors = True

        channel = self._makeOne()
        channel.adj = adj

        def log_info(msg, level):
            self.assertEqual(level, 'error')
            self.assertIn('exception', msg)

        channel.log_info = log_info

        class MyException(Exception):
            pass

        try:
            raise MyException()
        except MyException:
            channel.handle_comm_error()

    def test_handle_comm_err_no_logging(self):
        from zope.server.adjustments import Adjustments
        adj = Adjustments()
        adj.log_socket_errors = False

        channel = self._makeOne()
        channel.adj = adj

        closed = []

        def close():
            closed.append(True)

        channel.close = close

        class MyException(Exception):
            pass

        try:
            raise MyException()
        except MyException:
            channel.handle_comm_error()

        self.assertEqual([True], closed)

    def test_handle_error_reraise(self):

        class MyExit(SystemExit):
            pass

        class MyKB(KeyboardInterrupt):
            pass

        channel = self._makeOne()

        for e in (MyExit, MyKB):
            try:
                raise e()
            except e:
                with self.assertRaises(e):
                    channel.handle_error()

    def test_service_exception(self):
        channel = self._makeOne()

        class MyException(Exception):
            pass

        class Task:

            def service(self):
                raise MyException()

        task = Task()

        channel.tasks = [task]

        class Server:

            tasks = ()

            def addTask(self, t):
                self.tasks += (t,)

        channel.server = Server()

        # Exception propagates
        with self.assertRaises(MyException):
            channel.service()

        # and task is queue again
        self.assertEqual(channel.server.tasks, (channel,))

    def test_cancel(self):
        channel = self._makeOne()
        channel.set_sync()
        self.assertFalse(channel.async_mode)
        channel.running_tasks = True

        class Task:

            cancelled = False

            def cancel(self):
                self.cancelled = True

        task = Task()

        channel.tasks = [task]

        channel.cancel()

        self.assertTrue(task.cancelled)
        self.assertFalse(channel.running_tasks)
        self.assertTrue(channel.async_mode)

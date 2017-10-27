import unittest
import logging
from io import BytesIO, StringIO

from zope.server.taskthreads import ThreadedTaskDispatcher


# By using io.BytesIO() instead of cStringIO.StringIO() on Python 2 we make
# sure we're not trying to accidentally print unicode to stdout/stderr.
NativeStringIO = BytesIO if str is bytes else StringIO


class CountingDict(dict):
    """A dict that decrements values on every .get()"""

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        if key in self:
            self[key] -= 1
        return value

class QueueStub(object):
    def __init__(self, items=()):
        self.items = list(items)
    def get(self):
        return self.items.pop(0)

class TaskStub(object):
    def service(self):
        raise Exception('testing exception handling')


class TestExceptionLogging(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger('zope.server.taskthreads')
        self.logbuf = NativeStringIO()
        self.good_handler = logging.StreamHandler(self.logbuf)
        self.logger.addHandler(self.good_handler)
        self.bad_handler = logging.Handler()
        # test.bad_handler.emit() raises, which is what we want
        self.logger.addHandler(self.bad_handler)

    def tearDown(self):
        self.logger.removeHandler(self.bad_handler)
        self.logger.removeHandler(self.good_handler)


    def test_handlerThread_logs_exceptions_that_happen_during_exception_logging(self):
        # Test that ThreadedTaskDispatcher.handlerThread doesn't terminate silently

        dispatcher = ThreadedTaskDispatcher()
        dispatcher.threads = CountingDict({42: 1})
        dispatcher.queue = QueueStub([TaskStub()])

        with self.assertRaises(NotImplementedError):
            dispatcher.handlerThread(42)

        # It's important that exceptions in the thread main loop get
        # logged, not just exceptions that happen while handling tasks

        logged = self.logbuf.getvalue().rstrip()
        self.assertIn("Exception during task\nTraceback", logged)

        self.assertIn("Exception: testing exception handling", logged)
        self.assertIn("Exception in thread main loop\nTraceback", logged)
        self.assertIn(
            "NotImplementedError: emit must be implemented by Handler subclasses",
            logged)

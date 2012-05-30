import doctest
import logging
from cStringIO import StringIO

from zope.server.taskthreads import ThreadedTaskDispatcher


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


def setUp(test):
    test.logger = logging.getLogger('zope.server.taskthreads')
    test.logbuf = StringIO()
    test.good_handler = logging.StreamHandler(test.logbuf)
    test.logger.addHandler(test.good_handler)
    test.bad_handler = logging.Handler()
    # test.bad_handler.emit() raises, which is what we want
    test.logger.addHandler(test.bad_handler)
    test.globs['logbuf'] = test.logbuf

def tearDown(test):
    test.logger.removeHandler(test.bad_handler)
    test.logger.removeHandler(test.good_handler)


def doctest_handlerThread_logs_exceptions_that_happen_during_exception_logging():
    """Test that ThreadedTaskDispatcher.handlerThread doesn't terminate silently

        >>> dispatcher = ThreadedTaskDispatcher()
        >>> dispatcher.threads = CountingDict({42: 1})
        >>> dispatcher.queue = QueueStub([TaskStub()])
        >>> try: dispatcher.handlerThread(42)
        ... except: pass

    It's important that exceptions in the thread main loop get logged, not just
    exceptions that happen while handling tasks

        >>> print logbuf.getvalue(), # doctest: +ELLIPSIS
        Exception during task
        Traceback (most recent call last):
          ...
        Exception: testing exception handling
        Exception in thread main loop
        Traceback (most recent call last):
          ...
        NotImplementedError: emit must be implemented by Handler subclasses

    """


def test_suite():
    return doctest.DocTestSuite(setUp=setUp, tearDown=tearDown)


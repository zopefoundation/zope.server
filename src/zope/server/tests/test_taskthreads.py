import logging
import unittest
from io import StringIO

from zope.server.taskthreads import ThreadedTaskDispatcher


class CountingDict(dict):
    """A dict that decrements values on every .get()"""

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        if key in self:
            self[key] -= 1
        return value


class QueueStub:
    def __init__(self, items=()):
        self.items = list(items)

    def get(self):
        return self.items.pop(0)


class TaskStub:
    def service(self):
        raise Exception('testing exception handling')


class TestExceptionLogging(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger('zope.server.taskthreads')
        self.logbuf = StringIO()
        self.good_handler = logging.StreamHandler(self.logbuf)
        self.logger.addHandler(self.good_handler)
        self.bad_handler = logging.Handler()
        # test.bad_handler.emit() raises, which is what we want
        self.logger.addHandler(self.bad_handler)

    def tearDown(self):
        self.logger.removeHandler(self.bad_handler)
        self.logger.removeHandler(self.good_handler)

    def test_handlerThread_logs_exceptions_that_happen_during_exception_logging(self):  # noqa: E501 line too long
        # Test that ThreadedTaskDispatcher.handlerThread doesn't terminate
        # silently

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
            "NotImplementedError: emit must be implemented by Handler"
            " subclasses", logged)


class TestThreadedDispatcher(unittest.TestCase):

    def test_handlerThread_exits_while_running(self):

        dispatcher = ThreadedTaskDispatcher()

        class Task:

            def service(self):
                del dispatcher.threads[42]

        dispatcher.threads[42] = True
        dispatcher.queue.put(Task())
        dispatcher.handlerThread(42)

        self.assertEqual({}, dispatcher.threads)

    def test_addTask_None(self):
        with self.assertRaises(ValueError):
            ThreadedTaskDispatcher().addTask(None)

    def test_addTask_no_defer(self):
        class Task:

            cancel_called = False

            def cancel(self):
                self.cancel_called = True

        task = Task()

        with self.assertRaises(AttributeError):
            ThreadedTaskDispatcher().addTask(task)

        self.assertTrue(task.cancel_called)

    def test_shutdown_with_threads_still_running(self):

        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler('zope.server.taskthreads')

        dispatcher = ThreadedTaskDispatcher()
        dispatcher.threads[42] = 1

        dispatcher.shutdown(timeout=-1)

        self.assertIn("1 thread(s) still running", str(handler))

    def test_shutdown_cancel_pending(self):

        dispatcher = ThreadedTaskDispatcher()

        class Task:

            canceled = False

            def cancel(self):
                self.canceled = True
                from queue import Empty

                # We cheat to be able to catch the exception handler
                raise Empty()

        task = Task()
        dispatcher.queue.put(task)
        self.assertEqual(1, dispatcher.getPendingTasksEstimate())
        dispatcher.shutdown()

        self.assertTrue(task.canceled)
        self.assertEqual(0, dispatcher.getPendingTasksEstimate())

    def test_setThreadCount_adjust_twice(self):
        dispatcher = ThreadedTaskDispatcher()

        dispatcher.setThreadCount(1)
        self.assertEqual(1, len(dispatcher.threads))

        dispatcher.setThreadCount(2)
        self.assertEqual(2, len(dispatcher.threads))

        dispatcher.shutdown()

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Threaded Task Dispatcher
"""
import logging
import threading
from queue import Empty
from queue import Queue
from time import sleep
from time import time

from zope.interface import implementer

from zope.server.interfaces import ITaskDispatcher


log = logging.getLogger(__name__)


@implementer(ITaskDispatcher)
class ThreadedTaskDispatcher:
    """A Task Dispatcher that creates a thread for each task."""

    stop_count = 0  # Number of threads that will stop soon.

    def __init__(self):
        self.threads = {}  # { thread number -> 1 }
        self.queue = Queue()
        self.thread_mgmt_lock = threading.Lock()

    def handlerThread(self, thread_no):
        threads = self.threads
        try:
            while threads.get(thread_no):
                task = self.queue.get()
                if task is None:
                    # Special value: kill this thread.
                    break
                try:
                    task.service()
                except:  # noqa: E722 do not use bare 'except'
                    log.exception('Exception during task')
        except:  # noqa: E722 do not use bare 'except'
            log.exception('Exception in thread main loop')
        finally:
            mlock = self.thread_mgmt_lock
            with mlock:
                self.stop_count -= 1
                try:
                    del threads[thread_no]
                except KeyError:
                    pass

    def setThreadCount(self, count):
        """See zope.server.interfaces.ITaskDispatcher"""
        mlock = self.thread_mgmt_lock
        with mlock:
            threads = self.threads
            thread_no = 0
            running = len(threads) - self.stop_count
            while running < count:
                # Start threads.
                while thread_no in threads:
                    thread_no = thread_no + 1
                threads[thread_no] = 1
                running += 1
                t = threading.Thread(target=self.handlerThread,
                                     args=(thread_no,),
                                     name='zope.server-%d' % thread_no)
                t.setDaemon(True)
                t.start()
                thread_no = thread_no + 1
            if running > count:
                # Stop threads.
                to_stop = running - count
                self.stop_count += to_stop
                for _n in range(to_stop):
                    self.queue.put(None)
                    running -= 1

    def addTask(self, task):
        """See zope.server.interfaces.ITaskDispatcher"""
        if task is None:
            raise ValueError("No task passed to addTask().")
        # assert ITask.providedBy(task)
        try:
            task.defer()
            self.queue.put(task)
        except:  # noqa: E722 do not use bare 'except'
            task.cancel()
            raise

    def shutdown(self, cancel_pending=True, timeout=5):
        """See zope.server.interfaces.ITaskDispatcher"""
        self.setThreadCount(0)
        # Ensure the threads shut down.
        threads = self.threads
        expiration = time() + timeout
        while threads:
            if time() >= expiration:
                log.error("%d thread(s) still running", len(threads))
                break
            sleep(0.1)
        if cancel_pending:
            # Cancel remaining tasks.
            try:
                queue = self.queue
                while not queue.empty():
                    task = queue.get()
                    if task is not None:
                        task.cancel()
            except Empty:
                pass

    def getPendingTasksEstimate(self):
        """See zope.server.interfaces.ITaskDispatcher"""
        return self.queue.qsize()

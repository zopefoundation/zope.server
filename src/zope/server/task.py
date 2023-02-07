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
"""
Abstract implementation of ITask.

"""
import time


class AbstractTask:
    """
    An abstract task providing a framework for the common
    parts of implementing a Task.
    """

    close_on_finish = 0
    start_time = None

    def __init__(self, channel):
        self.channel = channel

    def service(self):
        """
        Called to execute the task.

        Subclasses must implement :meth:`_do_service`
        """
        try:
            try:
                self.start()
                self._do_service()
                self.finish()
            except OSError:
                self.close_on_finish = 1
                if self.channel.adj.log_socket_errors:
                    raise
            except:  # noqa: E722 do not use bare 'except'
                exc = getattr(self.channel, 'exception', None)
                if exc is not None:
                    exc()
                else:
                    raise
        finally:
            if self.close_on_finish:
                self.cancel()

    def _do_service(self):
        raise NotImplementedError()

    def cancel(self):
        """See ITask"""
        self.channel.close_when_done()

    def defer(self):
        """See ITask"""
        # Does nothing

    def start(self):
        now = time.time()
        self.start_time = now

    def finish(self):
        hit_log = self.channel.server.hit_log
        if hit_log is not None:
            hit_log.log(self)

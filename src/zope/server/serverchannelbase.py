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
"""Server-Channel Base Class

This module provides a base implementation for the server channel. It can only
be used as a mix-in to actual server channel implementations.
"""
import asyncore
import sys
import time
from threading import Lock

from zope.interface import implementer

from zope.server.dualmodechannel import DualModeChannel
from zope.server.interfaces import IServerChannel
from zope.server.interfaces import ITask


# task_lock is useful for synchronizing access to task-related attributes.
task_lock = Lock()


@implementer(IServerChannel, ITask)
class ServerChannelBase(DualModeChannel):
    """Base class for a high-performance, mixed-mode server-side channel."""

    # See zope.server.interfaces.IServerChannel
    parser_class = None       # Subclasses must provide a parser class
    task_class = None         # ... and a task class.

    active_channels = {}        # Class-specific channel tracker
    next_channel_cleanup = [0]  # Class-specific cleanup time
    proto_request = None      # A request parser instance
    last_activity = 0         # Time of last activity
    tasks = None  # List of channel-related tasks to execute
    running_tasks = False  # True when another thread is running tasks

    #
    # ASYNCHRONOUS METHODS (including __init__)
    #

    def __init__(self, server, conn, addr, adj=None):
        """See async.dispatcher"""
        DualModeChannel.__init__(self, conn, addr, adj)
        self.server = server
        self.last_activity = t = self.creation_time
        self.check_maintenance(t)

    def add_channel(self, map=None):
        """See async.dispatcher

        This hook keeps track of opened channels.
        """
        DualModeChannel.add_channel(self, map)
        self.__class__.active_channels[self._fileno] = self

    def del_channel(self, map=None):
        """See async.dispatcher

        This hook keeps track of closed channels.
        """
        DualModeChannel.del_channel(self, map)
        ac = self.__class__.active_channels
        fd = self._fileno
        if fd in ac:
            del ac[fd]

    def check_maintenance(self, now):
        """See async.dispatcher

        Performs maintenance if necessary.
        """
        ncc = self.__class__.next_channel_cleanup
        if now < ncc[0]:
            return
        ncc[0] = now + self.adj.cleanup_interval
        self.maintenance()

    def maintenance(self):
        """See async.dispatcher

        Kills off dead connections.
        """
        self.kill_zombies()

    def kill_zombies(self):
        """See async.dispatcher

        Closes connections that have not had any activity in a while.

        The timeout is configured through adj.channel_timeout (seconds).
        """
        now = time.time()
        cutoff = now - self.adj.channel_timeout
        # channel.close calls channel.del_channel, which can change
        # the size of the map.
        for channel in list(self.active_channels.values()):
            if (channel is not self and not channel.running_tasks and
                    channel.last_activity < cutoff):
                channel.close()

    def received(self, data):
        """See async.dispatcher

        Receives input asynchronously and send requests to
        handle_request().
        """
        preq = self.proto_request
        while data:
            if preq is None:
                preq = self.parser_class(self.adj)
            n = preq.received(data)
            if preq.completed:
                # The request is ready to use.
                self.proto_request = None
                if not preq.empty:
                    self.handle_request(preq)
                preq = None
            else:
                self.proto_request = preq
            if n >= len(data):
                break
            data = data[n:]

    def handle_request(self, req):
        """Create and queues a task for processing a request.

        Subclasses may override this method to handle some requests
        immediately in the main async thread.
        """
        task = self.task_class(self, req)
        self.queue_task(task)

    def handle_error(self):
        """See async.dispatcher

        Handles program errors (not communication errors)
        """
        t, v = sys.exc_info()[:2]
        if issubclass(t, (SystemExit, KeyboardInterrupt)):
            raise
        asyncore.dispatcher.handle_error(self)

    def handle_comm_error(self):
        """See async.dispatcher

        Handles communication errors (not program errors)
        """
        if self.adj.log_socket_errors:
            self.handle_error()
        else:
            # Ignore socket errors.
            self.close()

    #
    # BOTH MODES
    #

    def queue_task(self, task):
        """Queue a channel-related task to be executed in another thread."""
        start = False
        with task_lock:
            if self.tasks is None:
                self.tasks = []
            self.tasks.append(task)
            if not self.running_tasks:
                self.running_tasks = True
                start = True

        if start:
            self.set_sync()
            self.server.addTask(self)

    #
    # ITask implementation.  Delegates to the queued tasks.
    #

    def service(self):
        """Execute all pending tasks"""
        while True:
            task = None
            with task_lock:
                if self.tasks:
                    task = self.tasks.pop(0)
                else:
                    # No more tasks
                    self.running_tasks = False
                    self.set_async()
                    break

            try:
                task.service()
            except:  # noqa: E722 do not use bare 'except'
                # propagate the exception, but keep executing tasks
                self.server.addTask(self)
                raise

    def cancel(self):
        """Cancel all pending tasks"""
        with task_lock:
            old = () if not self.tasks else list(self.tasks)
            self.tasks = []
            self.running_tasks = False

        try:
            for task in old:
                task.cancel()
        finally:
            self.set_async()

    def defer(self):
        pass


try:
    from zope.testing.cleanup import addCleanUp
except ImportError:  # pragma: no cover
    pass
else:
    # Tests are very bad about actually closing
    # all the channels that they create. This leads to
    # an ever growing active_channels map.
    def _clean_active_channels():
        for c in list(ServerChannelBase.active_channels.values()):
            try:
                c.close()
            except BaseException:  # pragma: no cover
                pass
        ServerChannelBase.active_channels.clear()
    addCleanUp(_clean_active_channels)

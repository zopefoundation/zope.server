##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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

$Id$
"""
import os
import time
import sys
import asyncore
from thread import allocate_lock
from zope.interface import implements

from zope.server.dualmodechannel import DualModeChannel
from zope.server.interfaces import IServerChannel

# Synchronize access to the "running_tasks" attributes.
running_lock = allocate_lock()


class ServerChannelBase(DualModeChannel, object):
    """Base class for a high-performance, mixed-mode server-side channel."""

    implements(IServerChannel)

    # See zope.server.interfaces.IServerChannel
    parser_class = None       # Subclasses must provide a parser class
    task_class = None         # ... and a task class.

    active_channels = {}        # Class-specific channel tracker
    next_channel_cleanup = [0]  # Class-specific cleanup time

    proto_request = None      # A request parser instance
    ready_requests = None     # A list
    # ready_requests must always be empty when not running tasks.
    last_activity = 0         # Time of last activity
    running_tasks = 0         # boolean: true when any task is being executed

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
        for channel in self.active_channels.values():
            if (channel is not self and not channel.running_tasks and
                channel.last_activity < cutoff):
                channel.close()

    def received(self, data):
        """See async.dispatcher

        Receive input asynchronously and send requests to
        receivedCompleteRequest().
        """
        preq = self.proto_request
        while data:
            if preq is None:
                preq = self.parser_class(self.adj)
            n = preq.received(data)
            if preq.completed:
                # The request is ready to use.
                if not preq.empty:
                    self.receivedCompleteRequest(preq)
                preq = None
                self.proto_request = None
            else:
                self.proto_request = preq
            if n >= len(data):
                break
            data = data[n:]

    def receivedCompleteRequest(self, req):
        """See async.dispatcher

        If there are tasks running or requests on hold, queue
        the request, otherwise execute it.
        """
        do_now = 0
        running_lock.acquire()
        try:
            if self.running_tasks:
                # A task thread is working.  It will read from the queue
                # when it is finished.
                rr = self.ready_requests
                if rr is None:
                    rr = []
                    self.ready_requests = rr
                rr.append(req)
            else:
                # Do it now.
                do_now = 1
        finally:
            running_lock.release()
        if do_now:
            task = self.process_request(req)
            if task is not None:
                self.start_task(task)

    def start_task(self, task):
        """See async.dispatcher

        Starts the given task.

        *** For thread safety, this should only be called from the main
        (async) thread. ***"""
        if self.running_tasks:
            # Can't start while another task is running!
            # Otherwise two threads would work on the queue at the same time.
            raise RuntimeError, 'Already executing tasks'
        self.running_tasks = 1
        self.set_sync()
        self.server.addTask(task)

    def handle_error(self):
        """See async.dispatcher

        Handles program errors (not communication errors)
        """
        t, v = sys.exc_info()[:2]
        if t is SystemExit or t is KeyboardInterrupt:
            raise t, v
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
    # SYNCHRONOUS METHODS
    #

    def end_task(self, close):
        """Called at the end of a task and may launch another task.
        """
        if close:
            # Note that self.running_tasks is left on, which has the
            # side effect of preventing further requests from being
            # serviced even if more appear.  A good thing.
            self.close_when_done()
            return
        # Process requests held in the queue, if any.
        while 1:
            req = None
            running_lock.acquire()
            try:
                rr = self.ready_requests
                if rr:
                    req = rr.pop(0)
                else:
                    # No requests to process.
                    self.running_tasks = 0
            finally:
                running_lock.release()

            if req is not None:
                task = self.process_request(req)
                if task is not None:
                    # Add the new task.  It will service the queue.
                    self.server.addTask(task)
                    break
                # else check the queue again.
            else:
                # Idle -- Wait for another request on this connection.
                self.set_async()
                break

    #
    # BOTH MODES
    #

    def process_request(self, req):
        """Returns a task to execute or None if the request is quick and
        can be processed in the main thread.

        Override to handle some requests in the main thread.
        """
        return self.task_class(self, req)

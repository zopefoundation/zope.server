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
"""

$Id$
"""

import asyncore
import socket
from time import time

from zope.server import trigger
from zope.server.adjustments import default_adj
from zope.server.buffers import OverflowableBuffer


# Create the main trigger if it doesn't exist yet.
the_trigger = trigger.trigger()


class DualModeChannel(asyncore.dispatcher):
    """Channel that switches between asynchronous and synchronous mode.

    Call set_sync() before using a channel in a thread other than
    the thread handling the main loop.

    Call set_async() to give the channel back to the thread handling
    the main loop.
    """

    # will_close is set to 1 to close the socket.
    will_close = 0

    # boolean: async or sync mode
    async_mode = 1

    def __init__(self, conn, addr, adj=None):
        self.addr = addr
        if adj is None:
            adj = default_adj
        self.adj = adj
        self.outbuf = OverflowableBuffer(adj.outbuf_overflow)
        self.creation_time = time()
        asyncore.dispatcher.__init__(self, conn)

    #
    # ASYNCHRONOUS METHODS
    #

    def handle_close(self):
        self.close()

    def writable(self):
        if not self.async_mode:
            return 0
        return self.will_close or self.outbuf

    def handle_write(self):
        if not self.async_mode:
            return
        self.inner_handle_write()

    def inner_handle_write(self):
        if self.outbuf:
            try:
                self._flush_some()
            except socket.error:
                self.handle_comm_error()
        elif self.will_close:
            self.close()

    def readable(self):
        if not self.async_mode:
            return 0
        return not self.will_close

    def handle_read(self):
        if not self.async_mode:
            return
        self.inner_handle_read()

    def inner_handle_read(self):
        try:
            data = self.recv(self.adj.recv_bytes)
        except socket.error:
            self.handle_comm_error()
            return
        self.received(data)

    def received(self, data):
        """
        Override to receive data in async mode.
        """
        pass

    def handle_comm_error(self):
        """
        Designed for handling communication errors that occur
        during asynchronous operations *only*.  Probably should log
        this, but in a different place.
        """
        self.handle_error()

    def set_sync(self):
        """Switches to synchronous mode.

        The main thread will stop calling received().
        """
        self.async_mode = 0

    #
    # SYNCHRONOUS METHODS
    #

    def write(self, data):
        if data:
            self.outbuf.append(data)
        while len(self.outbuf) >= self.adj.send_bytes:
            # Send what we can without blocking.
            # We propagate errors to the application on purpose
            # (to stop the application if the connection closes).
            if not self._flush_some():
                break

    def flush(self, block=1):
        """Sends pending data.

        If block is set, this pauses the application.  If it is turned
        off, only the amount of data that can be sent without blocking
        is sent.
        """
        if not block:
            while self._flush_some():
                pass
            return
        blocked = 0
        try:
            while self.outbuf:
                # We propagate errors to the application on purpose.
                if not blocked:
                    self.socket.setblocking(1)
                    blocked = 1
                self._flush_some()
        finally:
            if blocked:
                self.socket.setblocking(0)

    def set_async(self):
        """Switches to asynchronous mode.

        The main thread will begin calling received() again.
        """
        self.async_mode = 1
        self.pull_trigger()

    #
    # METHODS USED IN BOTH MODES
    #

    def pull_trigger(self):
        """Wakes up the main loop.
        """
        the_trigger.pull_trigger()

    def _flush_some(self):
        """Flushes data.

        Returns 1 if some data was sent."""
        outbuf = self.outbuf
        if outbuf and self.connected:
            chunk = outbuf.get(self.adj.send_bytes)
            num_sent = self.send(chunk)
            if num_sent:
                outbuf.skip(num_sent, 1)
                return 1
        return 0

    def close_when_done(self):
        # We might be able close immediately.
        while self._flush_some():
            pass
        if not self.outbuf:
            # Quick exit.
            self.close()
        else:
            # Wait until outbuf is flushed.
            self.will_close = 1
            if not self.async_mode:
                self.async_mode = 1
                self.pull_trigger()


allocate_lock = None


class SimultaneousModeChannel(DualModeChannel):
    """Layer on top of DualModeChannel that allows communication in
    both the main thread and other threads at the same time.

    The channel operates in synchronous mode with an asynchronous
    helper.  The asynchronous callbacks empty the output buffer
    and fill the input buffer.
    """

    def __init__(self, conn, addr, adj=None):
        global allocate_lock
        if allocate_lock is None:
            from thread import allocate_lock

        # writelock protects all accesses to outbuf, since reads and
        # writes of buffers in this class need to be serialized.
        writelock = allocate_lock()
        self._writelock_acquire = writelock.acquire
        self._writelock_release = writelock.release
        self._writelock_locked = writelock.locked
        DualModeChannel.__init__(self, conn, addr, adj)

    #
    # ASYNCHRONOUS METHODS
    #

    def writable(self):
        return self.will_close or (
            self.outbuf and not self._writelock_locked())

    def handle_write(self):
        if not self._writelock_acquire(0):
            # A synchronous method is writing.
            return
        try:
            self.inner_handle_write()
        finally:
            self._writelock_release()

    def readable(self):
        return not self.will_close

    def handle_read(self):
        self.inner_handle_read()

    def set_sync(self):
        pass

    #
    # SYNCHRONOUS METHODS
    #

    def write(self, data):
        self._writelock_acquire()
        try:
            DualModeChannel.write(self, data)
        finally:
            self._writelock_release()

    def flush(self, block=1):
        self._writelock_acquire()
        try:
            DualModeChannel.flush(self, block)
        finally:
            self._writelock_release()

    def set_async(self):
        pass

    #
    # METHODS USED IN BOTH MODES
    #

    def close_when_done(self):
        self.will_close = 1
        self.pull_trigger()

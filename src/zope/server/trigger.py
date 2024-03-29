##############################################################################
#
# Copyright (c) 2001-2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import asyncore
import errno
import os
import socket
import struct
from threading import Lock


_ADDRESS_MASK = 256 ** struct.calcsize('P')


def positive_id(obj):
    """Return id(obj) as a non-negative integer."""
    # Note that the output depends on the size of void* on the platform.
    result = id(obj)
    if result < 0:
        result += _ADDRESS_MASK
        assert result > 0
    return result

# Original comments follow; they're hard to follow in the context of
# ZEO's use of triggers.  TODO:  rewrite from a ZEO perspective.

# Wake up a call to select() running in the main thread.
#
# This is useful in a context where you are using Medusa's I/O
# subsystem to deliver data, but the data is generated by another
# thread.  Normally, if Medusa is in the middle of a call to
# select(), new output data generated by another thread will have
# to sit until the call to select() either times out or returns.
# If the trigger is 'pulled' by another thread, it should immediately
# generate a READ event on the trigger object, which will force the
# select() invocation to return.
#
# A common use for this facility: letting Medusa manage I/O for a
# large number of connections; but routing each request through a
# thread chosen from a fixed-size thread pool.  When a thread is
# acquired, a transaction is performed, but output data is
# accumulated into buffers that will be emptied more efficiently
# by Medusa. [picture a server that can process database queries
# rapidly, but doesn't want to tie up threads waiting to send data
# to low-bandwidth connections]
#
# The other major feature provided by this class is the ability to
# move work back into the main thread: if you call pull_trigger()
# with a thunk argument, when select() wakes up and receives the
# event it will call your thunk from within that thread.  The main
# purpose of this is to remove the need to wrap thread locks around
# Medusa's data structures, which normally do not need them.  [To see
# why this is true, imagine this scenario: A thread tries to push some
# new data onto a channel's outgoing data queue at the same time that
# the main thread is trying to remove some]


class _triggerbase:
    """OS-independent base class for OS-dependent trigger class."""

    kind = None  # subclass must set to "pipe" or "loopback"; used by repr

    def __init__(self):
        self._closed = False

        # `lock` protects the `thunks` list from being traversed and
        # appended to simultaneously.
        self.lock = Lock()

        # List of no-argument callbacks to invoke when the trigger is
        # pulled.  These run in the thread running the asyncore mainloop,
        # regardless of which thread pulls the trigger.
        self.thunks = []

    def readable(self):
        return 1

    def writable(self):
        return 0

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    # Override the asyncore close() method, because it doesn't know about
    # (so can't close) all the gimmicks we have open.  Subclass must
    # supply a _close() method to do platform-specific closing work.  _close()
    # will be called iff we're not already closed.
    def close(self):
        if not self._closed:
            self._closed = True
            self.del_channel()
            self._close()  # subclass does OS-specific stuff

    def _close(self):    # see close() above; subclass must supply
        raise NotImplementedError

    def pull_trigger(self, thunk=None):
        if thunk:
            with self.lock:
                self.thunks.append(thunk)
        self._physical_pull()

    # Subclass must supply _physical_pull, which does whatever the OS
    # needs to do to provoke the "write" end of the trigger.
    def _physical_pull(self):
        raise NotImplementedError

    def handle_read(self):
        try:
            self.recv(8192)
        except OSError:
            return
        with self.lock:
            for thunk in self.thunks:
                try:
                    thunk()
                except:  # noqa: E722 do not use bare 'except'
                    _nil, t, v, tbinfo = asyncore.compact_traceback()
                    try:
                        print('exception in trigger thunk:'
                              ' (%s:%s %s)' % (t, v, tbinfo))
                    finally:
                        del t, v, tbinfo
            self.thunks = []

    def __repr__(self):
        return '<select-trigger ({}) at {:x}>'.format(
            self.kind, positive_id(self))


if hasattr(asyncore, 'file_dispatcher'):
    # asyncore.file_dispatcher does not exist on Windows
    class pipetrigger(_triggerbase, asyncore.file_dispatcher):
        kind = "pipe"

        def __init__(self):
            _triggerbase.__init__(self)
            r, self.trigger = os.pipe()
            asyncore.file_dispatcher.__init__(self, r)

            if self.socket.fd != r:
                # Starting in Python 2.6, the descriptor passed to
                # file_dispatcher gets duped and assigned to
                # self.socket.fd. This breaks the instantiation semantics and
                # is a bug imo.  I doubt it will get fixed, but maybe
                # it will. Who knows. For that reason, we test for the
                # fd changing rather than just checking the Python version.
                os.close(r)

        def _close(self):
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            if self.trigger is not None:
                os.close(self.trigger)
                self.trigger = None

        def _physical_pull(self):
            os.write(self.trigger, b'x')


class BindError(Exception):
    pass


class sockettrigger(_triggerbase, asyncore.dispatcher):
    # Windows version; uses just sockets, because a pipe isn't select'able
    # on Windows.
    kind = "loopback"

    ADDR_IN_USE_CODES = (getattr(errno, 'EADDRINUSE', -1),
                         getattr(errno, 'WSAEADDRINUSE', -1))

    def __init__(self):
        _triggerbase.__init__(self)

        # Get a pair of connected sockets.  The trigger is the 'w'
        # end of the pair, which is connected to 'r'.  'r' is put
        # in the asyncore socket map.  "pulling the trigger" then
        # means writing something on w, which will wake up r.

        w = socket.socket()
        # Disable buffering -- pulling the trigger sends 1 byte,
        # and we want that sent immediately, to wake up asyncore's
        # select() ASAP.
        w.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        count = 0
        while 1:
            count += 1
            # Bind to a local port; for efficiency, let the OS pick
            # a free port for us.
            # Unfortunately, stress tests showed that we may not
            # be able to connect to that port ("Address already in
            # use") despite that the OS picked it.  This appears
            # to be a race bug in the Windows socket implementation.
            # So we loop until a connect() succeeds (almost always
            # on the first try).  See the long thread at
            # http://mail.zope.org/pipermail/zope/2005-July/160433.html
            # for hideous details.
            a = socket.socket()
            a.bind(("127.0.0.1", 0))
            connect_address = a.getsockname()  # assigned (host, port) pair
            a.listen(1)
            try:
                self._connect_client(w, connect_address)
                break    # success
            except OSError as detail:
                if detail.args[0] not in self.ADDR_IN_USE_CODES:
                    # "Address already in use" is the only error
                    # I've seen on two WinXP Pro SP2 boxes, under
                    # Pythons 2.3.5 and 2.4.1.
                    # (Original commit: https://github.com/zopefoundation/ZEO/commit/c4f736a78ca6713fc3dec21f8aa1fa6f144dd82f)   # noqa: E501 line too long
                    a.close()
                    w.close()
                    raise
                # (10048, 'Address already in use')
                # assert count <= 2 # never triggered in Tim's tests
                if count >= 10:  # I've never seen it go above 2
                    a.close()
                    w.close()
                    raise BindError("Cannot bind trigger!")
                # Close `a` and try again.  Note:  I originally put a short
                # sleep() here, but it didn't appear to help or hurt.
                a.close()

        r, addr = a.accept()  # r becomes asyncore's (self.)socket
        a.close()
        self.trigger = w
        asyncore.dispatcher.__init__(self, r)

    def _connect_client(self, w, connect_address):
        w.connect(connect_address)

    def _close(self):
        # self.socket is r, and self.trigger is w, from __init__
        self.socket.close()
        self.trigger.close()

    def _physical_pull(self):
        self.trigger.send(b'x')


if os.name == 'posix':
    trigger = pipetrigger
else:  # pragma: no cover
    trigger = sockettrigger

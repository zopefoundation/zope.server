##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id: recvchannel.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""
from zope.server.serverchannelbase import ChannelBaseClass
from zope.server.buffers import OverflowableBuffer
from zope.server.interfaces import ITask


class RecvChannel(ChannelBaseClass):
    """ """

    complete_transfer = 0
    _fileno = None  # provide a default for asyncore.dispatcher._fileno

    def __init__ (self, control_channel, finish_args):
        self.control_channel = control_channel
        self.finish_args = finish_args
        self.inbuf = OverflowableBuffer(control_channel.adj.inbuf_overflow)
        ChannelBaseClass.__init__(self, None, None, control_channel.adj)
        # Note that this channel starts out in async mode.

    def writable (self):
        return 0

    def handle_connect (self):
        pass

    def received (self, data):
        if data:
            self.inbuf.append(data)

    def handle_close (self):
        """Client closed, indicating EOF."""
        c = self.control_channel
        task = FinishedRecvTask(c, self.inbuf, self.finish_args)
        self.complete_transfer = 1
        self.close()
        c.start_task(task)

    def close(self, *reply_args):
        try:
            c = self.control_channel
            if c is not None:
                self.control_channel = None
                if not self.complete_transfer and not reply_args:
                    # Not all data transferred
                    reply_args = ('TRANSFER_ABORTED',)
                c.notifyClientDCClosing(*reply_args)
        finally:
            if self.socket is not None:
                # XXX asyncore.dispatcher.close() doesn't like socket == None
                ChannelBaseClass.close(self)



class FinishedRecvTask:

    __implements__ = ITask

    def __init__(self, control_channel, inbuf, finish_args):
        self.control_channel = control_channel
        self.inbuf = inbuf
        self.finish_args = finish_args

    def service(self):
        """Called to execute the task.
        """
        close_on_finish = 0
        c = self.control_channel
        try:
            try:
                c.finishedRecv(self.inbuf, self.finish_args)
            except socket.error:
                close_on_finish = 1
                if c.adj.log_socket_errors:
                    raise
        finally:
            c.end_task(close_on_finish)


    def cancel(self):
        'See ITask'
        self.control_channel.close_when_done()


    def defer(self):
        'See ITask'
        pass

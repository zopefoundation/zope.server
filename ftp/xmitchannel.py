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

$Id: xmitchannel.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""

from zope.server.serverchannelbase import ChannelBaseClass


class XmitChannel(ChannelBaseClass):

    opened = 0
    _fileno = None  # provide a default for asyncore.dispatcher._fileno

    def __init__ (self, control_channel, ok_reply_args):
        self.control_channel = control_channel
        self.ok_reply_args = ok_reply_args
        self.set_sync()
        ChannelBaseClass.__init__(self, None, None, control_channel.adj)

    def _open(self):
        """Signal the client to open the connection."""
        self.opened = 1
        self.control_channel.reply(*self.ok_reply_args)
        self.control_channel.connectDataChannel(self)

    def write(self, data):
        if self.control_channel is None:
            raise IOError, 'Client FTP connection closed'
        if not self.opened:
            self._open()
        ChannelBaseClass.write(self, data)

    def readable(self):
        return not self.connected

    def handle_read(self):
        # This is only called when making the connection.
        try:
            self.recv(1)
        except:
            # The connection failed.
            self.close('NO_DATA_CONN')

    def handle_connect(self):
        pass

    def handle_comm_error(self):
        self.close('TRANSFER_ABORTED')

    def close(self, *reply_args):
        try:
            c = self.control_channel
            if c is not None:
                self.control_channel = None
                if not reply_args:
                    if not len(self.outbuf):
                        # All data transferred
                        if not self.opened:
                            # Zero-length file
                            self._open()
                        reply_args = ('TRANS_SUCCESS',)
                    else:
                        # Not all data transferred
                        reply_args = ('TRANSFER_ABORTED',)
                c.notifyClientDCClosing(*reply_args)
        finally:
            if self.socket is not None:
                # XXX asyncore.dispatcher.close() doesn't like socket == None
                ChannelBaseClass.close(self)


class ApplicationXmitStream:
    """Provide stream output, remapping close() to close_when_done().
    """

    def __init__(self, xmit_channel):
        self.write = xmit_channel.write
        self.flush = xmit_channel.flush
        self.close = xmit_channel.close_when_done

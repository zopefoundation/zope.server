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

$Id: passiveacceptor.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""

import asyncore
import socket


class PassiveAcceptor(asyncore.dispatcher):
    """This socket accepts a data connection, used when the server has
       been placed in passive mode.  Although the RFC implies that we
       ought to be able to use the same acceptor over and over again,
       this presents a problem: how do we shut it off, so that we are
       accepting connections only when we expect them?  [we can't]

       wuftpd, and probably all the other servers, solve this by
       allowing only one connection to hit this acceptor.  They then
       close it.  Any subsequent data-connection command will then try
       for the default port on the client side [which is of course
       never there].  So the 'always-send-PORT/PASV' behavior seems
       required.

       Another note: wuftpd will also be listening on the channel as
       soon as the PASV command is sent.  It does not wait for a data
       command first.

       --- we need to queue up a particular behavior:
       1) xmit : queue up producer[s]
       2) recv : the file object

       It would be nice if we could make both channels the same.
       Hmmm.."""

    __implements__ = asyncore.dispatcher.__implements__

    ready = None

    def __init__ (self, control_channel):
        asyncore.dispatcher.__init__ (self)
        self.control_channel = control_channel
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to an address on the interface that the
        # control connection is coming from.
        self.bind ( (self.control_channel.getsockname()[0], 0) )
        self.addr = self.getsockname()
        self.listen(1)


    def log (self, *ignore):
        pass


    def handle_accept (self):
        conn, addr = self.accept()
        conn.setblocking(0)
        dc = self.control_channel.client_dc
        if dc is not None:
            dc.set_socket(conn)
            dc.addr = addr
            dc.connected = 1
            self.control_channel.passive_acceptor = None
        else:
            self.ready = conn, addr
        self.close()

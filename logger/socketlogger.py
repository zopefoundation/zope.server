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

$Id: socketlogger.py,v 1.2 2002/12/25 14:15:27 jim Exp $
"""

import asynchat
import socket

from zope.server.interfaces.logger import IMessageLogger

class SocketLogger(asynchat.async_chat):
    """Log to a stream socket, asynchronously."""

    __implements__ = IMessageLogger

    def __init__(self, address):
        if type(address) == type(''):
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        self.connect(address)
        self.address = address

    def __repr__(self):
        return '<socket logger: address=%s>' % (self.address)

    def logMessage(self, message):
        'See IMessageLogger'
        if message[-2:] != '\r\n':
            self.socket.push(message + '\r\n')
        else:
            self.socket.push(message)

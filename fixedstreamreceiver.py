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

$Id: fixedstreamreceiver.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""

from zope.server.interfaces import IStreamConsumer


class FixedStreamReceiver:

    __implements__ = IStreamConsumer

    # See IStreamConsumer
    completed = 0

    def __init__(self, cl, buf):
        self.remain = cl
        self.buf = buf

    def received(self, data):
        'See IStreamConsumer'
        rm = self.remain
        if rm < 1:
            self.completed = 1  # Avoid any chance of spinning
            return 0
        datalen = len(data)
        if rm <= datalen:
            self.buf.append(data[:rm])
            self.remain = 0
            self.completed = 1
            return rm
        else:
            self.buf.append(data)
            self.remain -= datalen
            return datalen

    def getfile(self):
        return self.buf.getfile()
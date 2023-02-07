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
"""Line Command Parser
"""
from zope.interface import implementer

from zope.server.interfaces import IStreamConsumer


@implementer(IStreamConsumer)
class LineCommandParser:
    """Line Command parser. Arguments are left alone for now."""

    # See IStreamConsumer
    completed = 0
    inbuf = b''
    cmd = ''
    args = ''
    empty = 0

    max_line_length = 1024  # Not a hard limit

    def __init__(self, adj):
        """
        adj is an Adjustments object.
        """
        self.adj = adj

    def received(self, data):
        'See IStreamConsumer'
        if self.completed:
            return 0  # Can't consume any more.
        pos = data.find(b'\n')
        datalen = len(data)
        if pos < 0:
            self.inbuf = self.inbuf + data
            if len(self.inbuf) > self.max_line_length:
                # Don't accept any more.
                self.completed = 1
            return datalen
        else:
            # Line finished.
            s = data[:pos + 1]
            self.inbuf = self.inbuf + s
            self.completed = 1
            line = self.inbuf.strip()
            line = line.decode('utf-8')
            self.parseLine(line)
            return len(s)

    def parseLine(self, line):
        parts = line.split(' ', 1)
        if len(parts) == 2:
            self.cmd, self.args = parts
        else:
            self.cmd = parts[0]

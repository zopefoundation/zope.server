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
"""Data Chunk Receiver
"""

from zope.interface import implementer

from zope.server.interfaces import IStreamConsumer
from zope.server.utilities import find_double_newline


@implementer(IStreamConsumer)
class ChunkedReceiver:

    # Here's the production for a chunk:
    # (http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html)
    #   chunk          = chunk-size [ chunk-extension ] CRLF
    #                    chunk-data CRLF
    #   chunk-size     = 1*HEX
    #   chunk-extension= *( ";" chunk-ext-name [ "=" chunk-ext-val ] )
    #   chunk-ext-name = token
    #   chunk-ext-val  = token | quoted-string

    # This implementation is quite lax on what it will accept, and is
    # probably even vulnerable to malicious input (denial of service due to
    # space exhaustion) on carefully crafted badly formed chunk
    # control lines.

    chunk_remainder = 0
    control_line = b''
    all_chunks_received = 0
    trailer = b''
    completed = 0

    # max_control_line = 1024
    # max_trailer = 65536

    def __init__(self, buf):
        self.buf = buf

    def received(self, s):
        # Returns the number of bytes consumed.
        if self.completed:
            return 0
        orig_size = len(s)
        while s:
            rm = self.chunk_remainder
            if rm > 0:
                # Receive the remainder of a chunk.
                to_write = s[:rm]
                self.buf.append(to_write)
                written = len(to_write)
                s = s[written:]
                self.chunk_remainder -= written
            elif not self.all_chunks_received:
                # Receive a control line.
                s = self.control_line + s
                pos = s.find(b'\n')
                if pos < 0:
                    # Control line not finished.
                    self.control_line = s
                    s = b''
                else:
                    # Control line finished.
                    line = s[:pos]
                    s = s[pos + 1:]
                    self.control_line = b''
                    line = line.strip()
                    if line:
                        # Begin a new chunk.
                        semi = line.find(b';')
                        if semi >= 0:
                            # discard extension info.
                            line = line[:semi]
                        sz = int(line.strip(), 16)  # hexadecimal
                        if sz > 0:
                            # Start a new chunk.
                            self.chunk_remainder = sz
                        else:
                            # Finished chunks.
                            self.all_chunks_received = 1
                    # else expect a control line.
            else:
                # Receive the trailer.
                trailer = self.trailer + s
                if trailer.startswith(b'\r\n'):
                    # No trailer.
                    self.completed = 1
                    return orig_size - (len(trailer) - 2)
                if trailer.startswith(b'\n'):
                    # No trailer.
                    self.completed = 1
                    return orig_size - (len(trailer) - 1)
                pos = find_double_newline(trailer)
                if pos < 0:
                    # Trailer not finished.
                    self.trailer = trailer
                    s = b''
                else:
                    # Finished the trailer.
                    self.completed = 1
                    self.trailer = trailer[:pos]
                    return orig_size - (len(trailer) - pos)
        return orig_size

    def getfile(self):
        return self.buf.getfile()

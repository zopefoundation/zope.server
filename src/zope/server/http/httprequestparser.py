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
"""HTTP Request Parser

This server uses asyncore to accept connections and do initial
processing but threads to do work.
"""
import re
import sys
from io import BytesIO
from urllib.parse import unquote
from urllib.parse import urlsplit

from zope.interface import implementer

from zope.server.buffers import OverflowableBuffer
from zope.server.fixedstreamreceiver import FixedStreamReceiver
from zope.server.interfaces import IStreamConsumer
from zope.server.utilities import find_double_newline


PY3 = sys.version_info >= (3, )


@implementer(IStreamConsumer)
class HTTPRequestParser:
    """A structure that collects the HTTP request.

    Once the stream is completed, the instance is passed to
    a server task constructor.
    """

    # Parsing status
    completed = 0  # Set once request is completed.
    empty = 0        # Set if no request was made.
    in_header = False

    header_plus = b''
    chunked = 0
    content_length = 0
    body_rcv = None

    # Data from parsing. native strings.
    first_line = ''
    header = ''
    command = ''
    uri = ''
    version = ''
    proxy_scheme = None
    proxy_netloc = None
    path = None
    fragment = None
    query = None

    # headers is a mapping containing native string keys translated to
    # uppercase with dashes turned into underscores. The values
    # are also native strings.

    def __init__(self, adj):
        """
        adj is an Adjustments object.
        """
        self.headers = {}
        self.adj = adj

    def received(self, data):
        """
        Receives the HTTP stream for one request.
        Returns the number of bytes consumed.
        Sets the completed flag once both the header and the
        body have been received.
        """
        if self.completed:
            return 0  # Can't consume any more.
        datalen = len(data)
        br = self.body_rcv
        if br is None:
            # In header.
            s = self.header_plus + data
            index = find_double_newline(s)
            if index >= 0:
                # Header finished.
                header_plus = s[:index]
                consumed = len(data) - (len(s) - index)
                self.in_header = 0
                # Remove preceeding blank lines.
                header_plus = header_plus.lstrip()
                if not header_plus:
                    self.empty = 1
                    self.completed = 1
                else:
                    self.parse_header(header_plus)
                    if self.body_rcv is None:
                        self.completed = 1
                return consumed
            else:
                # Header not finished yet.
                self.header_plus = s
                return datalen
        else:
            # In body.
            consumed = br.received(data)
            if br.completed:
                self.completed = 1
            return consumed

    def parse_header(self, header_plus):
        """
        Parses the header_plus block of text (the headers plus the
        first line of the request).
        """
        index = header_plus.find(b'\n')
        if index >= 0:
            first_line = header_plus[:index].rstrip()
            header = header_plus[index + 1:]
        else:
            first_line = header_plus.rstrip()
            header = b''
        if PY3:
            first_line = first_line.decode('latin1')
            header = header.decode('latin1')
        self.first_line = first_line
        self.header = header

        lines = self.get_header_lines()
        headers = self.headers
        for line in lines:
            index = line.find(':')
            if index > 0:
                key = line[:index]
                value = line[index + 1:].strip()
                key1 = key.upper().replace('-', '_')
                # If a header already exists, we append subsequent values
                # seperated by a comma. Applications already need to handle
                # the comma seperated values, as HTTP front ends might do
                # the concatenation for you (behavior specified in RFC2616).
                try:
                    headers[key1] += ', %s' % value
                except KeyError:
                    headers[key1] = value
            # else there's garbage in the headers?

        assert isinstance(self.first_line, str)
        command, uri, version = self.crack_first_line()
        self.command = command or ''
        self.uri = uri or ''
        self.version = version
        self.split_uri()

        if version == '1.1':
            te = headers.get('TRANSFER_ENCODING', '')
            if te == 'chunked':
                from zope.server.http.chunking import ChunkedReceiver
                self.chunked = 1
                buf = OverflowableBuffer(self.adj.inbuf_overflow)
                self.body_rcv = ChunkedReceiver(buf)
        if not self.chunked:
            try:
                cl = int(headers.get('CONTENT_LENGTH', 0))
            except ValueError:
                cl = 0
            self.content_length = cl
            if cl > 0:
                buf = OverflowableBuffer(self.adj.inbuf_overflow)
                self.body_rcv = FixedStreamReceiver(cl, buf)

    def get_header_lines(self):
        """
        Splits the header into lines, putting multi-line headers together.
        """
        r = []
        lines = self.header.split('\n')
        for line in lines:
            if line and line[0] in ' \t':
                r[-1] = r[-1] + line[1:]
            else:
                r.append(line)
        return r

    first_line_re = re.compile(
        '([^ ]+) ((?:[^ :?#]+://[^ ?#/]*(?:[0-9]{1,5})?)?[^ ]+)'
        '(( HTTP/([0-9.]+))$|$)')

    def crack_first_line(self):
        method = uri = version = None

        r = self.first_line
        m = self.first_line_re.match(r)

        if m is not None and m.end() == len(r):
            if m.group(3):
                version = m.group(5)
            method = m.group(1).upper()
            uri = m.group(2)

        return (method, uri, version)

    def split_uri(self):
        (self.proxy_scheme, self.proxy_netloc, path, self.query,
         self.fragment) = urlsplit(self.uri)
        if path and '%' in path:
            path = unquote(path)
        self.path = path
        if self.query == '':
            self.query = None

    def getBodyStream(self):
        body_rcv = self.body_rcv
        if body_rcv is not None:
            return body_rcv.getfile()
        return BytesIO(b'')

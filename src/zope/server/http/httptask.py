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
"""HTTP Task

An HTTP task that can execute an HTTP request with the help of the channel and
the server it belongs to.
"""

from zope.interface import implementer
from zope.publisher.interfaces.http import IHeaderOutput

from zope.server.http.http_date import build_http_date
from zope.server.interfaces import ITask
from zope.server.task import AbstractTask


rename_headers = {
    'CONTENT_LENGTH': 'CONTENT_LENGTH',
    'CONTENT_TYPE': 'CONTENT_TYPE',
    'CONNECTION': 'CONNECTION_TYPE',
}


@implementer(ITask, IHeaderOutput)  # + IOutputStream
class HTTPTask(AbstractTask):
    """An HTTP task accepts a request and writes to a channel.

    Subclass this and override the execute() method.
    """

    instream = None
    close_on_finish = 1
    status = '200'
    reason = 'OK'
    wrote_header = 0
    accumulated_headers = None
    bytes_written = 0
    auth_user_name = ''
    cgi_env = None

    def __init__(self, channel, request_data):
        # request_data is a httprequestparser.HTTPRequestParser
        AbstractTask.__init__(self, channel)
        self.request_data = request_data
        self.response_headers = {}
        version = request_data.version
        if version not in ('1.0', '1.1'):
            # fall back to a version we support.
            version = '1.0'
        self.version = version

    def _do_service(self):
        self.channel.server.executeRequest(self)

    def setResponseStatus(self, status, reason):
        """See zope.publisher.interfaces.http.IHeaderOutput"""
        self.status = status
        self.reason = reason

    def setResponseHeaders(self, mapping):
        """See zope.publisher.interfaces.http.IHeaderOutput"""
        self.response_headers.update(mapping)

    def appendResponseHeaders(self, lst):
        """See zope.publisher.interfaces.http.IHeaderOutput"""
        accum = self.accumulated_headers
        if accum is None:
            self.accumulated_headers = accum = []
        accum.extend(lst)

    def wroteResponseHeader(self):
        """See zope.publisher.interfaces.http.IHeaderOutput"""
        return self.wrote_header

    def setAuthUserName(self, name):
        """See zope.publisher.interfaces.http.IHeaderOutput"""
        self.auth_user_name = name

    def prepareResponseHeaders(self):
        version = self.version
        # Figure out whether the connection should be closed.
        connection = self.request_data.headers.get('CONNECTION', '').lower()
        close_it = 0
        response_headers = self.response_headers
        accumulated_headers = self.accumulated_headers
        if accumulated_headers is None:
            accumulated_headers = []

        if version == '1.0':
            if connection == 'keep-alive':
                if 'Content-Length' not in response_headers:
                    close_it = 1
                else:
                    response_headers['Connection'] = 'Keep-Alive'
            else:
                close_it = 1
        elif version == '1.1':
            if 'connection: close' in (header.lower() for header in
                                       accumulated_headers):
                close_it = 1
            if connection == 'close':
                close_it = 1
            elif 'Transfer-Encoding' in response_headers:
                if response_headers['Transfer-Encoding'] != 'chunked':
                    close_it = 1
            elif self.status == '304':
                # Replying with headers only.
                pass
            elif 'Content-Length' not in response_headers:
                # accumulated_headers is a simple list, we need to cut off
                # the value of content-length manually
                if 'content-length' not in (header[:14].lower() for header in
                                            accumulated_headers):
                    close_it = 1
            # under HTTP 1.1 keep-alive is default, no need to set the header
        else:
            # Close if unrecognized HTTP version.
            close_it = 1

        self.close_on_finish = close_it
        if close_it:
            self.response_headers['Connection'] = 'close'

        # Set the Server and Date field, if not yet specified. This is needed
        # if the server is used as a proxy.
        if 'server' not in (header[:6].lower() for header in
                            accumulated_headers):
            self.response_headers['Server'] = self.channel.server.SERVER_IDENT
        else:
            self.response_headers['Via'] = self.channel.server.SERVER_IDENT
        if 'date' not in (header[:4].lower() for header in
                          accumulated_headers):
            self.response_headers['Date'] = build_http_date(self.start_time)

    def buildResponseHeader(self):
        self.prepareResponseHeaders()
        first_line = f'HTTP/{self.version} {self.status} {self.reason}'
        lines = [first_line] + ['%s: %s' % hv
                                for hv in self.response_headers.items()]
        accum = self.accumulated_headers
        if accum is not None:
            lines.extend(accum)
        res = '%s\r\n\r\n' % '\r\n'.join(lines)
        return res.encode('utf-8')

    def getCGIEnvironment(self):
        """Return a CGI-like environment."""
        env = self.cgi_env
        if env is not None:
            # Return the cached copy.
            return env

        request_data = self.request_data
        path = request_data.path
        channel = self.channel
        server = channel.server

        while path and path.startswith('/'):
            path = path[1:]

        env = {}
        env['REQUEST_METHOD'] = request_data.command.upper()
        env['SERVER_PORT'] = str(server.port)
        env['SERVER_NAME'] = server.server_name
        env['SERVER_SOFTWARE'] = server.SERVER_IDENT
        env['SERVER_PROTOCOL'] = "HTTP/%s" % self.version
        env['CHANNEL_CREATION_TIME'] = str(channel.creation_time)
        env['SCRIPT_NAME'] = ''
        env['PATH_INFO'] = '/' + path
        env['QUERY_STRING'] = request_data.query or ''
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        addr = channel.addr[0]
        env['REMOTE_ADDR'] = addr

        # If the server has a resolver, try to get the
        # remote host from the resolver's cache.
        resolver = getattr(server, 'resolver', None)
        if resolver is not None:
            dns_cache = resolver.cache
            if addr in dns_cache:
                remote_host = dns_cache[addr][2]
                if remote_host is not None:
                    env['REMOTE_HOST'] = remote_host

        for key, value in request_data.headers.items():
            value = value.strip()
            mykey = rename_headers.get(key, None)
            if mykey is None:
                mykey = 'HTTP_%s' % key
            if mykey not in env:
                env[mykey] = value

        self.cgi_env = env
        return env

    def finish(self):
        if not self.wrote_header:
            self.write(b'')
        AbstractTask.finish(self)

    def write(self, data):
        channel = self.channel
        if not self.wrote_header:
            rh = self.buildResponseHeader()
            channel.write(rh)
            self.bytes_written += len(rh)
            self.wrote_header = 1
        if data:
            self.bytes_written += channel.write(data)

    def flush(self):
        self.channel.flush()

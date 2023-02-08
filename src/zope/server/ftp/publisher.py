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
"""Zope Publisher-based FTP Server

This FTP server uses the Zope 3 Publisher to execute commands.
"""
import posixpath
from io import BytesIO

from zope.interface import implementer
from zope.publisher.publish import publish

from zope.server.ftp.server import FTPServer
from zope.server.interfaces.ftp import IFileSystem
from zope.server.interfaces.ftp import IFileSystemAccess


@implementer(IFileSystem)
class PublisherFileSystem:
    """Generic Publisher FileSystem implementation."""

    def __init__(self, credentials, request_factory):
        self.credentials = credentials
        self.request_factory = request_factory

    def type(self, path):
        if path == '/':
            return 'd'

        return self._execute(path, 'type')

    def readfile(self, path, outstream, start=0, end=None):
        return self._execute(path, 'readfile',
                             outstream=outstream, start=start, end=end)

    _name = None
    for _name in ('names', 'ls'):
        f = locals()[_name] = (
            lambda self, path, filter=None, _name=_name: self._execute(
                path,
                _name,
                split=False,
                filter=filter))
        f.__name__ = _name

    for _name in ('lsinfo', 'mtime', 'size', 'mkdir', 'remove', 'rmdir'):
        f = locals()[_name] = (
            lambda self, path, _name=_name: self._execute(path, _name))
        f.__name__ = _name
    del _name

    def rename(self, old, new):
        """See IWriteFileSystem"""
        old = self._translate(old)
        new = self._translate(new)
        path0, old = posixpath.split(old)
        path1, new = posixpath.split(new)
        assert path0 == path1
        return self._execute(path0, 'rename', split=False, old=old, new=new)

    def writefile(self, path, instream, start=None, end=None, append=False):
        """See IWriteFileSystem"""
        return self._execute(
            path, 'writefile',
            instream=instream, start=start, end=end, append=append)

    def writable(self, path):
        """See IWriteFileSystem"""
        return self._execute(path, 'writable')

    def _execute(self, path, command, split=True, **kw):
        env = {}
        env.update(kw)
        env['command'] = command

        path = self._translate(path)

        if split:
            env['path'], env['name'] = posixpath.split(path)
        else:
            env['path'] = path

        env['credentials'] = self.credentials
        request = self.request_factory(BytesIO(b''), env)

        # Note that publish() calls close() on request, which deletes the
        # response from the request, so that we need to keep track of it.
        # agroszer: 2008.feb.1.: currently the above seems not to be true
        # request will KEEP the response on close()
        # even more if a retry occurs in the publisher,
        # the response will be LOST, so we must accept the returned request
        request = publish(request)
        return request.response.getResult()

    def _translate(self, path):
        # Normalize
        path = posixpath.normpath(path)
        if path.startswith('..'):
            # Someone is trying to get lower than the permitted root.
            # We just ignore it.
            path = '/'
        return path


class PublisherFTPServer(FTPServer):
    """Generic FTP Server"""

    def __init__(self, request_factory, name, ip, port, *args, **kw):
        fs_access = PublisherFileSystemAccess(request_factory)
        super().__init__(ip, port, fs_access, *args, **kw)


@implementer(IFileSystemAccess)
class PublisherFileSystemAccess:

    def __init__(self, request_factory):
        self.request_factory = request_factory

    def authenticate(self, credentials):
        # We can't actually do any authentication initially, as the
        # user may not be defined at the root.
        pass

    def open(self, credentials):
        return PublisherFileSystem(credentials, self.request_factory)

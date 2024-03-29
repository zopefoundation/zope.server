##############################################################################
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""Demo file-system implementation, for testing
"""
import posixpath

from zope.interface import implementer
from zope.security.interfaces import Unauthorized

from zope.server.interfaces.ftp import IFileSystem
from zope.server.interfaces.ftp import IFileSystemAccess


execute = 1
read = 2
write = 4


class File:
    type = 'f'
    modified = None

    def __init__(self):
        self.access = {'anonymous': read}

    def accessable(self, user, access=read):
        return (
            user == 'root'
            or (self.access.get(user, 0) & access)
            or (self.access.get('anonymous', 0) & access)
        )

    def grant(self, user, access):
        self.access[user] = self.access.get(user, 0) | access

    def revoke(self, user, access):
        self.access[user] = self.access.get(user, 0) ^ access


class Directory(File):

    type = 'd'

    def __init__(self):
        super().__init__()
        self.files = {}

    def get(self, name, default=None):
        return self.files.get(name, default)

    def __getitem__(self, name):
        return self.files[name]

    def __setitem__(self, name, v):
        self.files[name] = v

    def __delitem__(self, name):  # pragma: no cover
        del self.files[name]

    def __contains__(self, name):
        return name in self.files

    def __iter__(self):
        return iter(self.files)


@implementer(IFileSystem)
class DemoFileSystem:
    __doc__ = IFileSystem.__doc__

    File = File
    Directory = Directory

    def __init__(self, files, user=''):
        self.files = files
        self.user = user

    def get(self, path, default=None):

        while path.startswith('/'):
            path = path[1:]

        d = self.files
        if path:
            for name in path.split('/'):
                assert d.type == 'd', "wrong type"
                assert d.accessable(self.user)
                d = d.get(name)
                if d is None:
                    break

        return d

    def getany(self, path):
        d = self.get(path)
        if d is None:
            raise OSError("No such file or directory:", path)
        return d

    def getdir(self, path):
        d = self.getany(path)
        if d.type != 'd':
            raise AssertionError("Not a directory:", path)
        return d

    def getfile(self, path):
        d = self.getany(path)
        if d.type != 'f':
            raise AssertionError("Not a file:", path)
        return d

    def getwdir(self, path):
        d = self.getdir(path)
        if not d.accessable(self.user, write):
            raise OSError("Permission denied")
        return d

    def type(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = self.get(path)
        return getattr(f, 'type', None)

    def names(self, path, filter=None):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = list(self.getdir(path))
        assert filter is None, "no filter allowed"
        return f

    def _lsinfo(self, name, file):
        info = {
            'type': file.type,
            'name': name,
            'group_read': file.accessable(self.user, read),
            'group_write': file.accessable(self.user, write),
        }
        if file.type == 'f':
            info['size'] = len(file.data)
        if file.modified is not None:
            info['mtime'] = file.modified

        return info

    def ls(self, path, filter=None):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = self.getdir(path)
        assert filter is None
        return [
            self._lsinfo(name, f.files[name])
            for name in f
        ]

    def readfile(self, path, outstream, start=0, end=None):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = self.getfile(path)

        data = f.data
        if end is not None:
            data = data[:end]
        if start:
            data = data[start:]

        outstream.write(data)

    def lsinfo(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = self.getany(path)
        return self._lsinfo(posixpath.split(path)[1], f)

    def mtime(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        return self.getany(path).modified

    def size(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        f = self.getany(path)
        return len(getattr(f, 'data', b''))

    def mkdir(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        path, name = posixpath.split(path)
        d = self.getwdir(path)
        if name in d.files:
            raise OSError("Already exists:", name)
        newdir = self.Directory()
        newdir.grant(self.user, read | write)
        d.files[name] = newdir

    def remove(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        path, name = posixpath.split(path)
        d = self.getwdir(path)
        if name not in d.files:
            raise AssertionError("Not exists:", name)
        f = d.files[name]
        if f.type == 'd':
            raise AssertionError('Is a directory:', name)
        del d.files[name]

    def rmdir(self, path):
        "See zope.server.interfaces.ftp.IFileSystem"
        path, name = posixpath.split(path)
        d = self.getwdir(path)
        if name not in d.files:
            raise AssertionError("Not exists:", name)
        f = d.files[name]
        if f.type != 'd':
            raise AssertionError('Is not a directory:', name)
        del d.files[name]

    def rename(self, old, new):
        """See zope.server.interfaces.ftp.IFileSystem"""
        oldpath, oldname = posixpath.split(old)
        newpath, newname = posixpath.split(new)

        olddir = self.getwdir(oldpath)
        newdir = self.getwdir(newpath)

        if oldname not in olddir.files:
            raise AssertionError("Not exists:", oldname)
        if newname in newdir.files:
            raise AssertionError("Already exists:", newname)

        newdir.files[newname] = olddir.files[oldname]
        del olddir.files[oldname]

    def writefile(self, path, instream, start=None, end=None, append=False):
        """See zope.server.interfaces.ftp.IFileSystem"""
        path, name = posixpath.split(path)
        d = self.getdir(path)
        f = d.files.get(name)
        if f is None:
            d = self.getwdir(path)
            f = d.files[name] = self.File()
            f.grant(self.user, read | write)
        elif f.type != 'f':
            raise AssertionError("Can't overwrite a directory")

        if not f.accessable(self.user, write):
            raise AssertionError("Permission denied")

        if append:
            f.data += instream.read()
        else:

            if start:
                if start < 0:
                    raise AssertionError("Negative starting file position")
                prefix = f.data[:start]
                assert len(prefix) >= start
            else:
                prefix = b''
                start = 0

            if end:
                if end < 0:
                    raise AssertionError("Negative ending file position")
                length = end - start
                newdata = instream.read(length)

                f.data = prefix + newdata + f.data[start + len(newdata):]
            else:
                f.data = prefix + instream.read()

    def writable(self, path):
        """See zope.server.interfaces.ftp.IFileSystem"""
        path, name = posixpath.split(path)
        try:
            d = self.getdir(path)
        except OSError:
            return False
        if name not in d:
            return d.accessable(self.user, write)
        f = d[name]
        return f.type == 'f' and f.accessable(self.user, write)


@implementer(IFileSystemAccess)
class DemoFileSystemAccess:
    __doc__ = IFileSystemAccess.__doc__

    def __init__(self, files, users):
        self.files = files
        self.users = users

    def authenticate(self, credentials):
        """See zope.server.interfaces.ftp.IFileSystemAccess"""
        user, password = credentials
        if user != 'anonymous':
            if self.users.get(user) != password:
                raise Unauthorized
        return user

    def open(self, credentials):
        """See zope.server.interfaces.ftp.IFileSystemAccess"""
        user = self.authenticate(credentials)
        return DemoFileSystem(self.files, user)

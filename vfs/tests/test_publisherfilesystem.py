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

$Id: test_publisherfilesystem.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""


import unittest
from StringIO import StringIO

from zope.server.vfs.publisherfilesystem import PublisherFileSystem
from zope.publisher.vfs import VFSRequest
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces.vfs import IVFSFilePublisher
from zope.publisher.interfaces.vfs import IVFSDirectoryPublisher
from zope.publisher.publish import mapply

from zope.server.vfs.tests.writefilesystemtests import WriteFilesystemTests


class VFSPublication (DefaultPublication):
    # This class will not be needed if we move callObject().

    def callObject(self, request, ob):
        method = getattr(ob, request.method)
        return mapply(method, request.getPositionalArguments(), request)

    def traverseName(self, request, ob, name):
        return ob.publishTraverse(request, name)


class TestFile:

    __implements__ = IVFSFilePublisher

    def __init__(self, data=''):
        self.data = data

    def publishTraverse(self, request, name):
        """See IVFSPublisher."""
        raise OSError, 'Cannot traverse TestFiles'

    def isdir(self):
        """See IVFSObjectPublisher."""
        return 0

    def isfile(self):
        """See IVFSObjectPublisher."""
        return 1

    def stat(self):
        """See IVFSObjectPublisher."""
        raise NotImplementedError

    def read(self, mode, outstream, start=0, end=-1):
        """See IVFSFilePublisher."""
        if end >= 0:
            s = self.data[start:end]
        else:
            s = self.data[start:]
        outstream.write(s)

    def write(self, mode, instream, start=0):
        """See IVFSFilePublisher."""
        s = instream.read()
        if 'a' in mode:
            self.data = self.data + s
        else:
            self.data = self.data[:start] + s + self.data[start + len(s):]




class TestDirectory:

    __implements__ = IVFSDirectoryPublisher

    def __init__(self, items={}):
        self.items = items.copy()

    def publishTraverse(self, request, name):
        """See IVFSPublisher."""
        return self.items[name]

    def isdir(self):
        """See IVFSObjectPublisher."""
        return 1

    def isfile(self):
        """See IVFSObjectPublisher."""
        return 0

    def stat(self):
        """See IVFSObjectPublisher."""
        raise NotImplementedError

    def exists(self, name):
        """See IVFSDirectoryPublisher."""
        return name in self.items

    def listdir(self, with_stats=0, pattern='*'):
        """See IVFSDirectoryPublisher."""
        if with_stats or pattern != '*':
            raise NotImplementedError
        return self.items.keys()

    def mkdir(self, name, mode=0777):
        """See IVFSDirectoryPublisher."""
        self.items[name] = TestDirectory()

    def remove(self, name):
        """See IVFSDirectoryPublisher."""
        del self.items[name]

    def rmdir(self, name):
        """See IVFSDirectoryPublisher."""
        del self.items[name]

    def rename(self, old, new):
        """See IVFSDirectoryPublisher."""
        if new in self.items:
            raise OSError, 'Name conflict'
        self.items[new] = self.items[old]
        del self.items[old]

    def writefile(self, name, mode, instream, start=0):
        """See IVFSDirectoryPublisher."""
        if not (name in self.items):
            self.items[name] = TestFile()
        self.items[name].write(mode, instream, start)

    def check_writable(self, name):
        """See IVFSDirectoryPublisher."""
        if name in self.items:
            if not self.items[name].isfile():
                raise IOError, 'Is not a file'


class PublisherFileSystemTests(unittest.TestCase, WriteFilesystemTests):
    """This test is constructed in a way that it builds up a directory
       structure, whcih is removed at the end.
    """

    filesystem_class = PublisherFileSystem

    check_exceptions = 1

    def setUp(self):

        app = TestDirectory()

        pub = VFSPublication(app)

        def request_factory(input_stream, output_steam, env):
            request = VFSRequest(input_stream, output_steam, env)
            request.setPublication(pub)
            return request

        self.filesystem = PublisherFileSystem(None, request_factory)
        self.filesystem.mkdir(self.dir_name)
        s = StringIO(self.file_contents)
        self.filesystem.writefile(self.file_name, 'w', s)

    def tearDown(self):
        pass



def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(PublisherFileSystemTests)

if __name__=='__main__':
    unittest.TextTestRunner().run( test_suite() )

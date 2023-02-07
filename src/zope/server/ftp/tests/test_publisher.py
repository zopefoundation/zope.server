##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Test the FTP publisher.
"""
import unittest
from io import BytesIO

from zope.publisher.publish import mapply

from . import demofs
from .fstests import FileSystemTests


class DemoFileSystem(demofs.DemoFileSystem):

    def rename(self, path, old, new):
        return demofs.DemoFileSystem.rename(
            self, "{}/{}".format(path, old), "{}/{}".format(path, new))


class Publication:

    def __init__(self, root):
        self.root = root

    def beforeTraversal(self, request):
        pass

    def getApplication(self, request):
        return self.root

    def afterTraversal(self, request, ob):
        pass

    def callObject(self, request, ob):
        command = getattr(ob, request.env['command'])
        if 'name' in request.env:
            request.env['path'] += "/" + request.env['name']
        return mapply(command, request=request.env)

    def afterCall(self, request, ob):
        pass

    def endRequest(self, request, ob):
        pass

    def handleException(self, object, request, info, retry_allowed=True):
        raise AssertionError("Not expecting an exception")


class Request:

    publication = None

    def __init__(self, input, env):
        self.env = env
        self.response = Response()
        self.user = env['credentials']
        del env['credentials']

    def processInputs(self):
        pass

    def traverse(self, root):
        root.user = self.user
        return root

    def close(self):
        pass


class Response:

    _result = None

    def setResult(self, result):
        self._result = result

    def getResult(self):
        return self._result


class RequestFactory:

    def __init__(self, root):
        self.pub = Publication(root)

    def __call__(self, input, env):
        r = Request(input, env)
        r.publication = self.pub
        return r


class TestPublisherFileSystem(FileSystemTests, unittest.TestCase):

    def setUp(self):
        root = demofs.Directory()
        root.grant('bob', demofs.write)
        fs = DemoFileSystem(root, 'bob')
        fs.mkdir(self.dir_name)
        fs.writefile(self.file_name, BytesIO(self.file_contents))
        fs.writefile(self.unwritable_filename, BytesIO(b"save this"))
        fs.get(self.unwritable_filename).revoke('bob', demofs.write)

        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.publisher import PublisherFileSystem
        self.filesystem = PublisherFileSystem('bob', RequestFactory(fs))

    def test_translate_parent(self):
        self.assertEqual('/', self.filesystem._translate('..'))


class TestPublisherFTPServer(unittest.TestCase):

    def test_construct(self):
        from zope.server.ftp.publisher import PublisherFTPServer

        class NonBinding(PublisherFTPServer):

            def bind(self, addr):
                return

        server = NonBinding(Request, 'name', None, 80, start=False)
        self.addCleanup(server.close)
        self.assertIsNotNone(server.fs_access)


class TestPublisherFileSystemAccess(unittest.TestCase):

    def test_authenticate(self):
        from zope.server.ftp.publisher import PublisherFileSystemAccess

        access = PublisherFileSystemAccess(None)
        self.assertIsNone(access.authenticate(None))

    def test_open(self):
        from zope.server.ftp.publisher import PublisherFileSystem
        from zope.server.ftp.publisher import PublisherFileSystemAccess
        access = PublisherFileSystemAccess(None)

        fs = access.open(None)
        self.assertIsInstance(fs, PublisherFileSystem)

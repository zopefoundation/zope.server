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

$Id: writefilesystemtests.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""
from cStringIO import StringIO

from zope.interface.verify import verifyClass
from zope.server.interfaces.vfs import IWriteFileSystem

from zope.server.vfs.tests.readfilesystemtests import ReadFilesystemTests


class WriteFilesystemTests (ReadFilesystemTests):
    """Tests of a writable and readable filesystem
    """

    def testRemove(self):
        self.failIf(not self.filesystem.exists(self.file_name))
        self.filesystem.remove(self.file_name)
        self.failIf(self.filesystem.exists(self.file_name))


    def testMkdir(self):
        path = self.dir_name + '/x'
        self.filesystem.mkdir(path)
        self.failUnless(self.filesystem.exists(path))
        self.failUnless(self.filesystem.isdir(path))


    def testRmdir(self):
        self.failIf(not self.filesystem.exists(self.dir_name))
        self.filesystem.remove(self.file_name)
        self.filesystem.rmdir(self.dir_name)
        self.failIf(self.filesystem.exists(self.dir_name))


    def testRename(self):
        self.filesystem.rename(self.file_name, self.file_name + '.bak')
        self.failIf(self.filesystem.exists(self.file_name))
        self.failIf(not self.filesystem.exists(self.file_name + '.bak'))


    def testWriteFile(self):
        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), self.file_contents)

        data = 'Always ' + self.file_contents
        s = StringIO(data)
        self.filesystem.writefile(self.file_name, 'wb', s)

        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), data)


    def testAppendToFile(self):
        data = ' again'
        s = StringIO(data)
        self.filesystem.writefile(self.file_name, 'ab', s)

        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), self.file_contents + data)


    def testWritePartOfFile(self):
        data = '123'
        s = StringIO(data)
        self.filesystem.writefile(self.file_name, 'r+b', s, 3)

        expect = self.file_contents[:3] + data + self.file_contents[6:]

        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), expect)


    def testWriteBeyondEndOfFile(self):
        partlen = len(self.file_contents) - 6
        data = 'daylight savings'
        s = StringIO(data)
        self.filesystem.writefile(self.file_name, 'r+b', s, partlen)

        expect = self.file_contents[:partlen] + data

        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), expect)


    def testWriteNewFile(self):
        s = StringIO(self.file_contents)
        self.filesystem.writefile(self.file_name + '.new', 'wb', s)

        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), self.file_contents)


    def testCheckWritable(self):
        if self.check_exceptions:
            # Can't overwrite a directory.
            self.assertRaises(
                IOError, self.filesystem.check_writable, self.dir_name)
        # Can overwrite a file.
        try:
            self.filesystem.check_writable(self.file_name)
        except IOError, v:
            self.fail('%s should be writable. (%s)' % (self.file_name, v))


    def testWriteInterface(self):
        class_ = self.filesystem.__class__
        self.failUnless(
            IWriteFileSystem.isImplementedByInstancesOf(class_))
        self.failUnless(verifyClass(IWriteFileSystem, class_))

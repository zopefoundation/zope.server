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
"""Abstract file-system tests
"""

from io import BytesIO

from zope.interface.verify import verifyObject

from zope.server.interfaces.ftp import IFileSystem


class FileSystemTests:
    """Tests of a readable filesystem"""

    filesystem = None
    dir_name = '/dir'
    file_name = '/dir/file.txt'
    unwritable_filename = '/dir/protected.txt'
    dir_contents = ['file.txt', 'protected.txt']
    file_contents = b'Lengthen your stride'

    def test_type(self):
        self.assertEqual(self.filesystem.type(self.dir_name), 'd')
        self.assertEqual(self.filesystem.type('/'), 'd')
        self.assertEqual(self.filesystem.type(self.file_name), 'f')

    def test_names(self):
        lst = self.filesystem.names(self.dir_name)
        lst.sort()
        self.assertEqual(lst, self.dir_contents)

    def test_readfile(self):
        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), self.file_contents)

    def testReadPartOfFile(self):
        s = BytesIO()
        self.filesystem.readfile(self.file_name, s, 2)
        self.assertEqual(s.getvalue(), self.file_contents[2:])

    def testReadPartOfFile2(self):
        s = BytesIO()
        self.filesystem.readfile(self.file_name, s, 1, 5)
        self.assertEqual(s.getvalue(), self.file_contents[1:5])

    def test_IFileSystemInterface(self):
        verifyObject(IFileSystem, self.filesystem)

    def testRemove(self):
        self.filesystem.remove(self.file_name)
        self.assertFalse(self.filesystem.type(self.file_name))

    def testMkdir(self):
        path = self.dir_name + '/x'
        self.filesystem.mkdir(path)
        self.assertEqual(self.filesystem.type(path), 'd')

    def testRmdir(self):
        self.filesystem.remove(self.file_name)
        self.filesystem.rmdir(self.dir_name)
        self.assertFalse(self.filesystem.type(self.dir_name))

    def testRename(self):
        self.filesystem.rename(self.file_name, self.file_name + '.bak')
        self.assertEqual(self.filesystem.type(self.file_name), None)
        self.assertEqual(self.filesystem.type(self.file_name + '.bak'), 'f')

    def testWriteFile(self):
        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), self.file_contents)

        data = b'Always ' + self.file_contents
        s = BytesIO(data)
        self.filesystem.writefile(self.file_name, s)

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), data)

    def testAppendToFile(self):
        data = b' again'
        s = BytesIO(data)
        self.filesystem.writefile(self.file_name, s, append=True)

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), self.file_contents + data)

    def testWritePartOfFile(self):
        data = b'123'
        s = BytesIO(data)
        self.filesystem.writefile(self.file_name, s, 3, 6)

        expect = self.file_contents[:3] + data + self.file_contents[6:]

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), expect)

    def testWritePartOfFile_and_truncate(self):
        data = b'123'
        s = BytesIO(data)
        self.filesystem.writefile(self.file_name, s, 3)

        expect = self.file_contents[:3] + data

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), expect)

    def testWriteBeyondEndOfFile(self):
        partlen = len(self.file_contents) - 6
        data = b'daylight savings'
        s = BytesIO(data)
        self.filesystem.writefile(self.file_name, s, partlen)

        expect = self.file_contents[:partlen] + data

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), expect)

    def testWriteNewFile(self):
        s = BytesIO(self.file_contents)
        self.filesystem.writefile(self.file_name + '.new', s)

        s = BytesIO()
        self.filesystem.readfile(self.file_name, s)
        self.assertEqual(s.getvalue(), self.file_contents)

    def test_writable(self):
        self.assertFalse(self.filesystem.writable(self.dir_name))
        self.assertFalse(self.filesystem.writable(self.unwritable_filename))
        self.assertTrue(self.filesystem.writable(self.file_name))
        self.assertTrue(self.filesystem.writable(self.file_name + '1'))

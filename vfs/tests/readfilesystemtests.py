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

$Id: readfilesystemtests.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""


import stat
from StringIO import StringIO

from zope.interface.verify import verifyClass
from zope.server.interfaces.vfs import IReadFileSystem


class ReadFilesystemTests:
    """Tests of a readable filesystem
    """

    filesystem = None
    dir_name  = '/dir'
    file_name = '/dir/file.txt'
    dir_contents = ['file.txt']
    file_contents = 'Lengthen your stride'

    check_exceptions = 1


    def testExists(self):
        self.failUnless(self.filesystem.exists(self.dir_name))
        self.failUnless(self.filesystem.exists(self.file_name))


    def testIsDir(self):
        self.failUnless(self.filesystem.isdir(self.dir_name))
        self.failUnless(not self.filesystem.isdir(self.file_name))


    def testIsFile(self):
        self.failUnless(self.filesystem.isfile(self.file_name))
        self.failUnless(not self.filesystem.isfile(self.dir_name))


    def testListDir(self):
        lst = self.filesystem.listdir(self.dir_name, 0)
        lst.sort()
        self.assertEqual(lst, self.dir_contents)


    def testReadFile(self):
        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s)
        self.assertEqual(s.getvalue(), self.file_contents)


    def testReadPartOfFile(self):
        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s, 2)
        self.assertEqual(s.getvalue(), self.file_contents[2:])


    def testReadPartOfFile2(self):
        s = StringIO()
        self.filesystem.readfile(self.file_name, 'rb', s, 1, 5)
        self.assertEqual(s.getvalue(), self.file_contents[1:5])


    def testReadInterface(self):
        class_ = self.filesystem.__class__
        self.failUnless(
            IReadFileSystem.isImplementedByInstancesOf(class_))
        self.failUnless(verifyClass(IReadFileSystem, class_))

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

$Id: posixfilesystemtests.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""


import stat

from zope.interface.verify import verifyClass
from zope.server.interfaces.vfs import IPosixFileSystem

from zope.server.vfs.tests.writefilesystemtests import WriteFilesystemTests


class PosixFilesystemTests (WriteFilesystemTests):
    """Tests of a writable and readable POSIX-compliant filesystem
    """

    def testChmod(self):
        old_mode = self.filesystem.stat(self.file_name)[stat.ST_MODE]
        new_mode = old_mode ^ 0444
        self.filesystem.chmod(self.file_name, new_mode)
        check_mode = self.filesystem.stat(self.file_name)[stat.ST_MODE]
        self.assertEqual(check_mode, new_mode)


    def testChown(self):
        self.filesystem.chown(self.file_name, 500, 500)
        s = self.filesystem.stat(self.file_name)
        self.assertEqual(s[stat.ST_UID], 500)
        self.assertEqual(s[stat.ST_GID], 500)


    def testMakeLink(self):
        self.filesystem.link(self.file_name, self.file_name + '.linked')
        self.failUnless(self.filesystem.exists(self.file_name + '.linked'))
        # Another test should test whether writing to one file
        # changes the other.


    def testMakeFifo(self):
        path = self.dir_name + '/fifo'
        self.filesystem.mkfifo(path)
        self.failUnless(self.filesystem.exists(path))
        # Another test should test the behavior of the fifo.


    def testMakeSymlink(self):
        self.filesystem.symlink(self.file_name, self.file_name + '.symlink')
        self.failUnless(self.filesystem.exists(self.file_name + '.symlink'))
        # Another test should test whether writing to one file
        # changes the other.


    def testPosixInterface(self):
        class_ = self.filesystem.__class__
        self.failUnless(
            IPosixFileSystem.isImplementedByInstancesOf(class_))
        self.failUnless(verifyClass(IPosixFileSystem, class_))

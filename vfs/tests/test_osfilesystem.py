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

$Id: test_osfilesystem.py,v 1.3 2003/01/30 15:52:57 jim Exp $
"""
import unittest
import os
import shutil
import tempfile
import datetime
fromts = datetime.datetime.fromtimestamp

from StringIO import StringIO

from zope.server.vfs.osfilesystem import OSFileSystem

from zope.server.vfs.tests.writefilesystemtests import WriteFilesystemTests


def joinToRoot(root, name):
    if name.startswith('/'):
        name = name[1:]
    return os.path.join(root, os.path.normpath(name))


class OSFileSystemTests(unittest.TestCase, WriteFilesystemTests):
    """This test is constructed in a way that it builds up a directory
       structure, whcih is removed at the end.
    """

    filesystem_class = OSFileSystem
    root = None

    def setUp(self):
        if self.root is None:
            self.root = tempfile.mktemp()
            self.filesystem = self.filesystem_class(self.root)

        os.mkdir(self.root)
        os.mkdir(joinToRoot(self.root, self.dir_name))
        f = open(joinToRoot(self.root, self.file_name), 'w')
        f.write(self.file_contents)
        f.close()


    def tearDown(self):

        shutil.rmtree(self.root)


    def testNormalize(self):

        def norm(p):
            return self.filesystem.normalize(p).replace(os.sep, '/')

        self.assertEqual(norm('/foo/bar//'), '/foo/bar')
        self.assertEqual(norm('/foo//bar'), '/foo/bar')
        self.assertEqual(norm('///foo/bar'), '/foo/bar')
        self.assertEqual(norm('///foo//bar////'), '/foo/bar')

        self.assertEqual(norm('../foo/bar'), '/')
        self.assertEqual(norm('..'), '/')
        self.assertEqual(norm('/..'), '/')
        self.assertEqual(norm('/foo/..'), '/')
        self.assertEqual(norm('/foo/../bar'), '/bar')
        self.assertEqual(norm('../../'), '/')

        self.assertEqual(norm('///../foo/bar'), '/foo/bar')
        self.assertEqual(norm('/foo/..///'), '/')
        self.assertEqual(norm('///foo/..//bar'), '/bar')
        self.assertEqual(norm('..///../'), '/')


    def testTranslate(self):

        self.assertEqual(self.filesystem.root, self.root)

        self.assertEqual(self.filesystem.translate('/foo/'),
                         os.path.join(self.root, 'foo'))
        self.assertEqual(self.filesystem.translate('/foo/bar'),
                         os.path.join(self.root, 'foo', 'bar'))
        self.assertEqual(self.filesystem.translate('foo/bar'),
                         os.path.join(self.root, 'foo', 'bar'))

    def testStat(self):
        stat = os.stat(joinToRoot(self.root, self.file_name))
        stat = stat[0:7] + (fromts(stat[7]), fromts(stat[8]), fromts(stat[9]))
        self.assertEqual(self.filesystem.stat(self.file_name), stat)




if 0 and os.name == 'posix':

    from zope.server.vfs.tests.posixfilesystemtests import PosixFilesystemTests

    class OSPosixFilesystemTests(OSFileSystemTests, PosixFilesystemTests):

        def testChown(self):
            # Disable this test, since it won't work unless you're root.
            return

    OSFileSystemTests = OSPosixFilesystemTests



def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(OSFileSystemTests)

if __name__=='__main__':
    unittest.TextTestRunner().run( test_suite() )

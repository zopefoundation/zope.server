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
"""Test the Demo Filesystem implementation.
"""
import unittest
from io import BytesIO

from . import demofs
from .fstests import FileSystemTests


class Test(FileSystemTests, unittest.TestCase):

    def setUp(self):
        root = demofs.Directory()
        root.grant('bob', demofs.write)
        fs = self.filesystem = demofs.DemoFileSystem(root, 'bob')
        fs.mkdir(self.dir_name)
        fs.writefile(self.file_name, BytesIO(self.file_contents))
        fs.writefile(self.unwritable_filename, BytesIO(b"save this"))
        fs.get(self.unwritable_filename).revoke('bob', demofs.write)

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
"""Implementation of IFilesystemAccess intended only for testing.

$Id: testfilesystemaccess.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""

from zope.server.interfaces.vfs import IFilesystemAccess
from zope.server.interfaces.vfs import IUsernamePassword
from zope.exceptions import Unauthorized


class TestFilesystemAccess:

    __implements__ = IFilesystemAccess

    passwords = {'foo': 'bar'}

    def __init__(self, fs):
        self.fs = fs

    def authenticate(self, credentials):
        if not IUsernamePassword.isImplementedBy(credentials):
            raise Unauthorized
        name = credentials.getUserName()
        if not (name in self.passwords):
            raise Unauthorized
        if credentials.getPassword() != self.passwords[name]:
            raise Unauthorized

    def open(self, credentials):
        self.authenticate(credentials)
        return self.fs

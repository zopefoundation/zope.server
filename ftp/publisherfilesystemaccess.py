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

$Id: publisherfilesystemaccess.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""

from cStringIO import StringIO
from zope.exceptions import Unauthorized
from zope.app.security.registries.principalregistry import principalRegistry

from zope.server.vfs.publisherfilesystem import PublisherFileSystem
from zope.server.interfaces.vfs import IFilesystemAccess
from zope.server.interfaces.vfs import IUsernamePassword


class PublisherFilesystemAccess:

    __implements__ = IFilesystemAccess

    def __init__(self, request_factory):
        self.request_factory = request_factory


    def authenticate(self, credentials):
        assert IUsernamePassword.isImplementedBy(credentials)
        env = {'credentials' : credentials}
        request = self.request_factory(StringIO(''), StringIO(), env)
        id = principalRegistry.authenticate(request)
        if id is None:
            raise Unauthorized


    def open(self, credentials):
        return PublisherFileSystem(credentials, self.request_factory)

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

$Id: usernamepassword.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""

from zope.server.interfaces.vfs import IUsernamePassword


class UsernamePassword:

    __implements__ = IUsernamePassword

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def getUserName(self):
        return self.username

    def getPassword(self):
        return self.password

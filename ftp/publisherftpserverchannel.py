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

$Id: publisherftpserverchannel.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""

from zope.server.ftp.ftpserverchannel import FTPServerChannel

class PublisherFTPServerChannel(FTPServerChannel):
    """The FTP Server Channel represents a connection to a particular
       client. We can therefore store information here."""

    __implements__ = FTPServerChannel.__implements__


    def authenticate(self):
        if self._getFilesystem()._authenticate():
            return 1, 'User successfully authenticated.'
        else:
            return 0, 'User could not be authenticated.'

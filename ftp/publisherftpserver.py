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

$Id: publisherftpserver.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""
from zope.server.ftp.ftpserver import FTPServer

from zope.server.ftp.publisherfilesystemaccess import PublisherFilesystemAccess

class PublisherFTPServer(FTPServer):
    """Generic FTP Server"""


    def __init__(self, request_factory, name, ip, port, *args, **kw):
        self.request_factory = request_factory
        fs_access = PublisherFilesystemAccess(request_factory)
        super(PublisherFTPServer, self).__init__(ip, port, fs_access,
                                                 *args, **kw)

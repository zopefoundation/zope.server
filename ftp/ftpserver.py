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

$Id: ftpserver.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""
import asyncore
from zope.server.ftp.ftpserverchannel import FTPServerChannel
from zope.server.serverbase import ServerBase
from zope.server.interfaces.vfs import IFilesystemAccess



class FTPServer(ServerBase):
    """Generic FTP Server"""

    channel_class = FTPServerChannel
    SERVER_IDENT = 'zope.server.ftp'


    def __init__(self, ip, port, fs_access, *args, **kw):

        assert IFilesystemAccess.isImplementedBy(fs_access)
        self.fs_access = fs_access

        super(FTPServer, self).__init__(ip, port, *args, **kw)


if __name__ == '__main__':
    from zope.server.taskthreads import ThreadedTaskDispatcher
    from zope.server.vfs.osfilesystem import OSFileSystem
    from zope.server.vfs.testfilesystemaccess import TestFilesystemAccess
    td = ThreadedTaskDispatcher()
    td.setThreadCount(4)
    fs = OSFileSystem('/')
    fs_access = TestFilesystemAccess(fs)
    FTPServer('', 8021, fs_access, task_dispatcher=td)
    try:
        while 1:
            asyncore.poll(5)
            print 'active channels:', FTPServerChannel.active_channels
    except KeyboardInterrupt:
        print 'shutting down...'
        td.shutdown()

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

$Id: vfs.py,v 1.2 2002/12/25 14:15:26 jim Exp $
"""

from zope.interface import Interface


# XXX These interfaces should be located in a more central location.
# (so I don't mind putting them together in one module for now ;-) )

class ICredentials(Interface):
    """Base interface for presentation of authentication credentials.

    Different kinds of credentials include username/password, client
    certificate, IP address and port, etc., including combinations.
    """


class IUsernamePassword(ICredentials):
    """A type of authentication credentials consisting of user name and
    password.  The most recognized form of credentials.
    """

    def getUserName():
        """Returns the user name presented for authentication.
        """

    def getPassword():
        """Returns the password presented for authentication.
        """


# XXX This interface should be in a more central location.

class IFilesystemAccess(Interface):
    """Provides authenticated access to a filesystem.
    """

    def authenticate(credentials):
        """Verifies filesystem access based on the presented credentials.

        Should raise Unauthorized if the user can not be authenticated.

        This method only checks general access and is not used for each
        call to open().  Rather, open() should do its own verification.
        """

    def open(credentials):
        """Returns an IReadFilesystem or IWriteFilesystem.

        Should raise Unauthorized if the user can not be authenticated.
        """


class IReadFileSystem(Interface):
    """We want to provide a complete wrapper around any and all read
       filesystem operations.

       Opening files for reading, and listing directories, should
       return a producer.

       All paths are POSIX paths, even when run on Windows,
       which mainly means that FS implementations always expect forward
       slashes, and filenames are case-sensitive.

       Note: A file system should *not* store any state!
    """

    def exists(path):
        """Test whether a path exists.
        """

    def isdir(path):
        """Test whether a path is a directory.
        """

    def isfile(path):
        """Test whether a path is a file.
        """

    def listdir(path, with_stats=0, pattern='*'):
        """Return a listing of the directory at 'path' The empty
           string indicates the current directory.  If 'with_stats' is set,
           instead return a list of (name, stat_info) tuples. All file
           names are filtered by the globbing pattern.  (See the 'glob'
           module in the Python standard library.)
        """
        return list(tuple(str, str))

    def readfile(path, mode, outstream, start=0, end=-1):
        """Outputs the file at path to a stream.
        """

    def stat(path):
        """Return the equivalent of os.stat() on the given path:

           (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)
        """


class IWriteFileSystem(Interface):
    """We want to provide a complete wrapper around any and all write
       filesystem operations.

       Notes:
         - A file system should *not* store any state!
         - Most of the commands copy the functionality given in os.
    """

    def mkdir(path, mode=777):
        """Create a directory.
        """

    def remove(path):
        """Remove a file. Same as unlink.
        """

    def rmdir(path):
        """Remove a directory.
        """

    def rename(old, new):
        """Rename a file or directory.
        """

    def writefile(path, mode, instream, start=0):
        """Write data to a file.
        """

    def check_writable(path):
        """Ensures a path is writable.  Throws an IOError if not."""


class IPosixFileSystem(IWriteFileSystem, IReadFileSystem):
    """
    """

    def chmod(path, mode):
        """Change the access permissions of a file.
        """

    def chown(path, uid, gid):
        """Change the owner and group id of path to numeric uid and gid.
        """

    def link(src, dst):
        """Create a heard link to a file.
        """

    def mkfifo(path, mode=777):
        """Create a FIFO (a POSIX named pipe).
        """

    def symlink(src, dst):
        """Create a symbolic link at dst pointing to src.
        """

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
"""Filesystem implementation for a real (unix-like) OS filesystem.

$Id: osfilesystem.py,v 1.2 2002/12/25 14:15:28 jim Exp $
"""
import os
import re
import stat
import datetime
import fnmatch
fromts = datetime.datetime.fromtimestamp

from zope.server.interfaces.vfs import IPosixFileSystem


class OSFileSystem(object):
    """Generic OS FileSystem implementation.

       The root of this file system is a string describing the path
       to the directory used as root.
    """

    __implements__ = IPosixFileSystem

    copy_bytes = 65536


    def __init__ (self, root):
        self.root = root

    def chmod(self, path, mode):
        'See IWriteFileSystem'
        p = self.translate (path)
        return os.chmod(p, mode)


    def chown(self, path, uid, gid):
        'See IWriteFileSystem'
        p = self.translate (path)
        return os.chown(p, uid, gid)


    def link(self, src, dst):
        'See IWriteFileSystem'
        src = self.translate(src)
        dst = self.translate(dst)
        return os.link(src, dst)


    def mkfifo(self, path, mode=6*2**6):
        'See IWriteFileSystem'
        return os.mkfifo(path, mode)


    def symlink(self, src, dst):
        'See IWriteFileSystem'
        src = self.translate(src)
        dst = self.translate(dst)
        return os.symlink(src, dst)

    def exists(self, path):
        'See IReadFileSystem'
        p = self.translate(path)
        return os.path.exists(p)


    def isdir(self, path):
        'See IReadFileSystem'
        p = self.translate(path)
        return os.path.isdir(p)


    def isfile(self, path):
        'See IReadFileSystem'
        p = self.translate(path)
        return os.path.isfile(p)


    def listdir(self, path, with_stats=0, pattern='*'):
        'See IReadFileSystem'
        p = self.translate(path)
        # list the directory's files
        ld = os.listdir(p)
        # filter them using the pattern
        ld = filter(lambda f, p=pattern, fnm=fnmatch.fnmatch: fnm(f, p), ld)
        # sort them alphabetically
        ld.sort()
        if not with_stats:
            result = ld
        else:
            result = []
            for file in ld:
                path = os.path.join(p, file)
                stat = safe_stat(path)
                if stat is not None:
                    result.append((file, stat))
        return result


    def readfile(self, path, mode, outstream, start=0, end=-1):
        'See IReadFileSystem'
        p = self.translate(path)
        instream = open(p, mode)
        if start:
            instream.seek(start)
        pos = start
        while end < 0 or pos < end:
            toread = self.copy_bytes
            if end >= 0:
                toread = min(toread, end - pos)
            data = instream.read(toread)
            if not data:
                break
            pos += len(data)
            outstream.write(data)


    def stat(self, path):
        'See IReadFileSystem'
        p = self.translate(path)
        stat = os.stat(p)
        return stat[0:6], fromts(stat[7]), fromts(stat[8]), fromts(stat[9])

    def mkdir(self, path, mode=6*2**6):
        'See IWriteFileSystem'
        p = self.translate(path)
        return os.mkdir(p, mode)


    def remove(self, path):
        'See IWriteFileSystem'
        p = self.translate (path)
        return os.remove(p)


    def rmdir(self, path):
        'See IWriteFileSystem'
        p = self.translate (path)
        return os.rmdir(p)


    def rename(self, old, new):
        'See IWriteFileSystem'
        old = self.translate(old)
        new = self.translate(new)
        return os.rename(old, new)


    def writefile(self, path, mode, instream, start=0):
        'See IWriteFileSystem'
        p = self.translate(path)
        outstream = open(p, mode)
        if start:
            outstream.seek(start)
        while 1:
            data = instream.read(self.copy_bytes)
            if not data:
                break
            outstream.write(data)

    def check_writable(self, path):
        'See IWriteFileSystem'
        p = self.translate(path)
        if os.path.exists(p):
            remove = 0
        else:
            remove = 1
        f = open(p, 'a')  # append mode
        f.close()
        if remove:
            os.remove(p)

    # utility methods

    def normalize(self, path):
        # watch for the ever-sneaky '/+' path element
        # XXX It is unclear why "/+" is dangerous.  It is definitely
        # unexpected.
        path = re.sub('/+', '/', path)
        path = os.path.normpath(path)
        if path.startswith('..'):
            # Someone is trying to get lower than the permitted root.
            # We just ignore it.
            path = os.sep
        return path


    def translate(self, path):
        """We need to join together three separate path components,
           and do it safely.  <real_root>/<path>
           use the operating system's path separator.

           We need to be extremly careful to include the cases where a hacker
           could attempt to a directory below root!
        """
        # Normalize the directory
        path = self.normalize(path)
        # Prepare for joining with root
        while path.startswith(os.sep):
            path = path[1:]
        # Join path with root
        return os.path.join(self.root, path)


    def __repr__(self):
        return '<OSFileSystem, root=%s>' % self.root



def safe_stat(path):
    try:
        stat = os.stat(path)
        return stat[:7] + (fromts(stat[7]), fromts(stat[8]), fromts(stat[9]))
    except OSError:
        return None

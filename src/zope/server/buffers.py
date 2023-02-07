##############################################################################
#
# Copyright (c) 2001-2004 Zope Foundation and Contributors.
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
"""Buffers
"""
import tempfile
from io import BytesIO


# copy_bytes controls the size of temp. strings for shuffling data around.
COPY_BYTES = 1 << 18  # 256K

# The maximum number of bytes to buffer in a simple string.
STRBUF_LIMIT = 8192


class FileBasedBuffer:

    remain = 0

    def __init__(self, file, from_buffer=None):
        self.file = file
        if from_buffer is not None:
            # This code base no longer uses this
            # function except tests that are designed
            # just to test it.
            from_file = from_buffer.getfile()
            read_pos = from_file.tell()
            from_file.seek(0)
            while 1:
                data = from_file.read(COPY_BYTES)
                if not data:
                    break
                file.write(data)
            self.remain = int(file.tell() - read_pos)
            from_file.seek(read_pos)
            file.seek(read_pos)

    def __len__(self):
        return self.remain

    def append(self, s):
        file = self.file
        read_pos = file.tell()
        file.seek(0, 2)
        file.write(s)
        file.seek(read_pos)
        self.remain = self.remain + len(s)

    def get(self, bytes=-1, skip=0):
        file = self.file
        if not skip:
            read_pos = file.tell()
        if bytes < 0:
            # Read all
            res = file.read()
        else:
            res = file.read(bytes)
        if skip:
            self.remain -= len(res)
        else:
            file.seek(read_pos)
        return res

    def skip(self, bytes, allow_prune=0):
        if self.remain < bytes:
            raise ValueError("Can't skip %d bytes in buffer of %d bytes" % (
                bytes, self.remain))
        self.file.seek(bytes, 1)
        self.remain = self.remain - bytes

    def newfile(self):
        raise NotImplementedError()

    def prune(self):
        file = self.file
        if self.remain == 0:
            read_pos = file.tell()
            file.seek(0, 2)
            sz = file.tell()
            file.seek(read_pos)
            if sz == 0:
                # Nothing to prune.
                return
        nf = self.newfile()
        while 1:
            data = file.read(COPY_BYTES)
            if not data:
                break
            nf.write(data)
        self.file.close()
        self.file = nf

    def getfile(self):
        return self.file

    def close(self):
        self.file.close()


class TempfileBasedBuffer(FileBasedBuffer):

    def __init__(self, from_buffer=None):
        FileBasedBuffer.__init__(self, self.newfile(), from_buffer)

    def newfile(self):
        return tempfile.TemporaryFile(mode='w+b',
                                      suffix='zope_server_buffer.tmp')


class StringIOBasedBuffer(FileBasedBuffer):

    def __init__(self, from_buffer=None):
        FileBasedBuffer.__init__(self, self.newfile(), from_buffer)

    def newfile(self):
        return BytesIO()


class OverflowableBuffer(TempfileBasedBuffer):
    """
    A buffer based on a :class:`tempfile.SpooledTemporaryFile`,
    buffering up to *overflow* (plus some extra) in memory, and
    automatically spooling that to disk when exceeded.

    .. versionchanged:: 4.0.0
       Re-implement in terms of ``SpooledTemporaryFile``.
       Internal attributes of this object such as ``overflowed`` and
       ``strbuf`` no longer exist.
    """

    def __init__(self, overflow):
        # overflow is the maximum to be stored in a SpooledTemporaryFile
        self.overflow = overflow + STRBUF_LIMIT
        TempfileBasedBuffer.__init__(self)

    def newfile(self):
        return tempfile.SpooledTemporaryFile(max_size=self.overflow,
                                             mode='w+b',
                                             suffix='zope_server_buffer.tmp')

    def getfile(self):
        # Return the underlying file object, not the spooled file
        # (despite the _ prefix, this is a documented attribute).
        # If we haven't rolled to disk, this will be the StringIO object.
        # This improves backwards compatibility for code that assumes
        # it can do getfile().getvalue() (which before would work for
        # small values)
        return self.file._file

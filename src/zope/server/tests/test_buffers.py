"""
Tests for buffers.py

"""

import unittest

from zope.server import buffers


class TestStringBuffer(unittest.TestCase):

    def _getFUT(self):
        return buffers.StringIOBasedBuffer

    def _makeOne(self):
        buf = self._getFUT()()
        self.addCleanup(buf.close)
        return buf

    def test_cannot_skip_empty(self):
        with self.assertRaises(ValueError):
            self._makeOne().skip(10)

    def test_prune_empty_does_nothing(self):
        buf = self._makeOne()
        f = buf.file
        buf.prune()
        self.assertIs(buf.file, f)

    def test_prune_copies_to_new_file(self):
        buf = self._makeOne()
        buf.append(b'data')
        f = buf.file
        buf.prune()
        self.assertIsNot(buf.file, f)

        buf.skip(-4)
        data = buf.get()
        self.assertEqual(b'data', data)
        # remain is now wrong-ish
        self.assertEqual(8, buf.remain)
        # and still
        data = buf.get(skip=True)
        self.assertEqual(b'data', data)
        self.assertEqual(4, buf.remain)

    def test_construct_from_buffer(self):
        buf1 = self._makeOne()
        buf1.append(b'data')

        buf2 = self._getFUT()(buf1)
        self.addCleanup(buf2.close)

        self.assertEqual(buf2.get(), b'data')


class TestTempfileBasedBuffer(TestStringBuffer):

    def _getFUT(self):
        return buffers.TempfileBasedBuffer

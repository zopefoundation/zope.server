"""
Tests for chunking.py

"""
import unittest

from zope.server.buffers import StringIOBasedBuffer
from zope.server.http import chunking


class TestChunkedReceiver(unittest.TestCase):

    def _makeOne(self):
        return chunking.ChunkedReceiver(StringIOBasedBuffer())

    def _do_test(self, data, expected=b'oh hai'):
        reader = self._makeOne()

        for d in (data,) if isinstance(data, bytes) else data:
            reader.received(d)

        self.assertEqual(reader.getfile().read(),
                         expected)

        # Now feed it one byte at a time.
        if isinstance(data, bytes):
            reader = self._makeOne()
            for c in data:
                # sigh. Python iterates bytes as ints
                c = bytes((c,))
                reader.received(c)
            self.assertEqual(reader.getfile().read(),
                             expected)
        return reader

    def test_simple_body(self):
        reader = self._do_test(b'2\r\noh\r\n4\r\n hai\r\n0\r\n\r\n')
        self.assertTrue(reader.completed)
        self.assertEqual(0, reader.received(b'abc'))

    def test_simple_body_no_trailer(self):
        reader = self._do_test(b'2\r\noh\r\n4\r\n hai\r\n0\n\r\n')
        self.assertTrue(reader.completed)
        self.assertEqual(0, reader.received(b'abc'))

        reader = self._do_test(b'2\r\noh\r\n4\r\n hai\r\n\r\n')
        self.assertFalse(reader.completed)
        self.assertEqual(3, reader.received(b'abc'))

    def test_quoted_ext(self):
        self._do_test(b'2;token="oh hi"\r\noh\r\n4\r\n hai\r\n0\r\n\r\n')

    def test_token_ext(self):
        self._do_test(b'2;token=oh_hi\r\noh\r\n4\r\n hai\r\n0\r\n\r\n')

    def test_incorrect_chunk_token_ext_too_long(self):
        # Most servers place limits on the size of tokens in chunks
        # they'll accept, but we don't. For example, this fails in
        # gevent.
        data = b'2;token=oh_hi\r\noh\r\n4\r\n hai\r\n0\r\n\r\n'
        data = data.replace(b'oh_hi', b'_oh_hi' * 4000)
        reader = self._do_test(data)
        self.assertTrue(reader.completed)

    def test_trailer_leading_bytes(self):
        reader = self._makeOne()
        reader.received(b'0\r\n')
        self.assertTrue(reader.all_chunks_received)
        self.assertFalse(reader.completed)
        self.assertEqual(0, reader.chunk_remainder)

        # Feed a trailer with no data
        reader.received(b'')

        self.assertTrue(reader.all_chunks_received)
        self.assertEqual(0, reader.chunk_remainder)
        self.assertFalse(reader.completed)

        # Feed a trailing with leading spaces but still a double newline.
        # We accept this as completed
        reader.received(b' \r\n\r\n')
        self.assertTrue(reader.completed)

    def test_trailer_single_newline(self):
        reader = self._makeOne()
        reader.received(b'0\r\n')
        self.assertTrue(reader.all_chunks_received)
        self.assertFalse(reader.completed)
        self.assertEqual(0, reader.chunk_remainder)

        # Feed a trailing with just a single newline.
        # We accept this as completed
        reader.received(b'\njunk')
        self.assertTrue(reader.completed)

"""
Tests for linecommandparser.py

"""
import unittest

from zope.server.linereceiver import linecommandparser


class TestLineCommandparser(unittest.TestCase):

    def test_received_completed(self):

        parser = linecommandparser.LineCommandParser(None)
        parser.completed = True
        self.assertEqual(0, parser.received(None))

    def test_line_too_long(self):
        parser = linecommandparser.LineCommandParser(None)
        parser.max_line_length = 1

        data = b'this data is too long for the line'
        x = parser.received(data)
        self.assertEqual(x, len(data))
        self.assertEqual(parser.inbuf, data)
        self.assertEqual(0, parser.received(None))

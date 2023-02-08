"""
Tests for utilities.py

"""

import unittest

from zope.server import utilities


class TestFunctions(unittest.TestCase):

    def test_find_double_newline_twice(self):
        s = b"abc\n\r\ndef\n\ngef"
        x = utilities.find_double_newline(s)
        self.assertEqual(x, 6)

# -*- coding: utf-8 -*-
"""
Tests for trigger.py

"""

import unittest

from zope.server import trigger

class TestFunctions(unittest.TestCase):

    def test_positive_id(self):

        trigger.id = lambda o: -42
        try:
            # This is possibly only correct on 64-bit platforms
            self.assertEqual(18446744073709551574L,
                             trigger.positive_id(None))
        finally:
            del trigger.id

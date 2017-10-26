# -*- coding: utf-8 -*-
"""
Tests for asyncerror.py

"""

import unittest
from zope.server.tests.asyncerror import AsyncoreErrorHook

class TestAsyncoreErrorHook(AsyncoreErrorHook,
                            unittest.TestCase):

    def test_handle_asynore_error(self):
        try:
            raise Exception()
        except Exception:
            with self.assertRaises(AssertionError):
                self.handle_asyncore_error()

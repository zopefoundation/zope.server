"""
Tests for asyncerror.py

"""

import unittest

from zope.server.tests.asyncerror import AsyncoreErrorHookMixin


class TestAsyncoreErrorHook(AsyncoreErrorHookMixin,
                            unittest.TestCase):

    def test_handle_asynore_error(self):
        try:
            raise Exception()
        except Exception:
            with self.assertRaises(AssertionError):
                self.handle_asyncore_error()

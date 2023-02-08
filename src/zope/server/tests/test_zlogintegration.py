"""
Tests for zlogintegration.py

"""

import unittest


class TestLogInfo(unittest.TestCase):

    def test_patched(self):
        import asyncore

        from zope.server import zlogintegration

        # dispatcher is a class, so this becomes an unbound method
        # on Python 2
        dispatcher_info = asyncore.dispatcher.log_info
        dispatcher_info = getattr(dispatcher_info, '__func__', dispatcher_info)
        self.assertEqual(dispatcher_info,
                         zlogintegration.log_info)

    def test_log_info(self):
        from zope.testing.loggingsupport import InstalledHandler

        from zope.server import zlogintegration

        handler = InstalledHandler('zope.server')
        try:
            zlogintegration.log_info(None, "Some Info")
        finally:
            handler.uninstall()

        self.assertEqual(1, len(handler.records))
        self.assertEqual("Some Info", str(handler.records[0].getMessage()))

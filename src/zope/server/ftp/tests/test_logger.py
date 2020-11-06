# -*- coding: utf-8 -*-
"""
Tests for logger.py

"""

import unittest

from zope.server.ftp import logger

from zope.testing import loggingsupport


class TestCommonFTPActivityLogger(unittest.TestCase):

    def test_log(self):
        class Task(object):
            class channel(object):
                username = 'user'
                cwd = '/'
                addr = ('localhost',)
            m_name = 'head'

        handler = loggingsupport.InstalledHandler("accesslog")
        self.addCleanup(handler.uninstall)

        cal = logger.CommonFTPActivityLogger()
        cal.log(Task)

        self.assertEqual(1, len(handler.records))
        self.assertIn('localhost', str(handler))
        self.assertIn('user', str(handler))

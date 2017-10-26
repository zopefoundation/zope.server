# -*- coding: utf-8 -*-
"""
Tests for logger.py

"""

import unittest

from zope.server.ftp import logger

class TestCommonFTPActivityLogger(unittest.TestCase):

    def test_log(self):
        class Task(object):
            class channel(object):
                username = 'user'
                cwd = '/'
                addr = ('localhost',)
            m_name = 'head'

        msgs = []
        class Output(object):
            def logMessage(self, msg):
                msgs.append(msg)

        output = Output()
        cal = logger.CommonFTPActivityLogger(output)
        cal.log(Task)

        self.assertEqual(1, len(msgs))
        self.assertIn('localhost', msgs[0])
        self.assertIn('user', msgs[0])

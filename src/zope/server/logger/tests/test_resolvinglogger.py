# -*- coding: utf-8 -*-
"""
Tests for resolvinglogger.py

"""
import unittest

from zope.server.logger import resolvinglogger

class TestResolvingLogger(unittest.TestCase):

    def test_log_request(self):
        class Logger(object):
            msgs = ()
            def logMessage(self, msg):
                self.msgs += (msg,)

        class Resolver(object):
            def resolve_ptr(self, ip, then):
                then('host', None, None)

        logger = Logger()
        rl = resolvinglogger.ResolvingLogger(Resolver(), logger)

        rl.logRequest(None, ' Message')
        self.assertEqual(logger.msgs,
                         ('host Message',))

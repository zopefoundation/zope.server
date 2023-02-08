##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Common Access Logger tests
"""
import logging
import unittest

import zope.server.http.commonaccesslogger


class CommonAccessLogger(
        zope.server.http.commonaccesslogger.CommonAccessLogger):
    def _localtime(self, when):
        assert when == 123456789
        return (1973, 11, 29, 21, 33, 9)


class TestCommonAccessLogger(unittest.TestCase):
    def test_default_constructor(self):
        from zope.server.logger.pythonlogger import PythonLogger
        logger = CommonAccessLogger()
        # CommonHitLogger is registered as an argumentless factory via
        # ZCML, so the defaults should be sensible
        self.assertIsInstance(logger.output, PythonLogger)
        self.assertEqual(logger.output.logger.name, 'accesslog')
        self.assertEqual(logger.output.level, logging.INFO)

    def test_compute_timezone_for_log_negative(self):
        tz = -3600
        self.assertEqual('+0100',
                         CommonAccessLogger.compute_timezone_for_log(tz))

    def test_compute_timezone_for_log_positive(self):
        tz = 3600
        self.assertEqual('-0100',
                         CommonAccessLogger.compute_timezone_for_log(tz))

    def test_log_date_string_daylight(self):
        import time
        orig_dl = time.daylight
        orig_az = time.altzone
        time.daylight = True
        time.altzone = -3600
        try:
            s = CommonAccessLogger().log_date_string(123456789)
        finally:
            time.daylight = orig_dl
            time.altzone = orig_az

        self.assertEqual(s, '29/Nov/1973:21:33:09 +0100')

    def test_log_date_string_non_daylight(self):
        import time
        orig_dl = time.daylight
        orig_tz = time.timezone
        time.daylight = False
        time.timezone = -3600
        try:
            s = CommonAccessLogger().log_date_string(123456789)
        finally:
            time.daylight = orig_dl
            time.timezone = orig_tz

        self.assertEqual(s, '29/Nov/1973:21:33:09 +0100')

    def test_log_request(self):
        import time

        from zope.testing import loggingsupport
        handler = loggingsupport.InstalledHandler("accesslog")
        self.addCleanup(handler.uninstall)

        class Resolver:
            def resolve_ptr(self, ip, then):
                then('host', None, None)

        class Task:
            channel = request_data = property(lambda s: s)
            headers = {}
            auth_user_name = None
            addr = ('localhost', )
            first_line = 'GET / HTTP/1.0'
            status = '200 OK'
            bytes_written = 10

        orig_t = time.time

        def t():
            return 123456789
        orig_dl = time.daylight
        orig_az = time.altzone
        time.daylight = True
        time.altzone = -3600
        time.time = t
        try:
            cal = CommonAccessLogger(resolver=Resolver())
            cal.log(Task())
        finally:
            time.daylight = orig_dl
            time.altzone = orig_az
            time.time = orig_t

        self.assertEqual(1, len(handler.records))
        self.assertEqual(
            'host - anonymous [29/Nov/1973:21:33:09 +0100]'
            ' "GET / HTTP/1.0" 200 OK 10 "" ""',
            handler.records[0].getMessage())

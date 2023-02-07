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
"""Test HTTP date converters
"""
import unittest

from zope.server.http import http_date


class Tests(unittest.TestCase):

    # test roundtrip conversion.
    def testDateRoundTrip(self):
        from time import time
        t = int(time())
        self.assertEqual(
            t,
            http_date.parse_http_date(http_date.build_http_date(t)))

    def test_cannot_parse(self):
        self.assertEqual(0, http_date.parse_http_date("Not Valid"))

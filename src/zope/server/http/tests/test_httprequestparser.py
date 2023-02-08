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
"""HTTP Request Parser tests
"""
import unittest

from zope.server.adjustments import Adjustments
from zope.server.http.httprequestparser import HTTPRequestParser


my_adj = Adjustments()


class Tests(unittest.TestCase):

    def setUp(self):
        self.parser = HTTPRequestParser(my_adj)

    def feed(self, data):
        parser = self.parser
        for _ in range(100):  # make sure we never loop forever
            consumed = parser.received(data)
            data = data[consumed:]
            if parser.completed:
                self.assertEqual(0, parser.received(b'nonsense data'))
                return
        raise AssertionError('Looping too far')

    def testSimpleGET(self):
        data = b"""\
GET /foobar HTTP/8.4
FirstName: mickey
lastname: Mouse
content-length: 7

Hello.
"""
        parser = self.parser
        self.feed(data)
        self.assertTrue(parser.completed)
        self.assertEqual(parser.version, '8.4')
        self.assertFalse(parser.empty)
        self.assertEqual(parser.headers,
                         {'FIRSTNAME': 'mickey',
                          'LASTNAME': 'Mouse',
                          'CONTENT_LENGTH': '7'})
        self.assertEqual(parser.path, '/foobar')
        self.assertEqual(parser.command, 'GET')
        self.assertEqual(parser.query, None)
        self.assertEqual(parser.proxy_scheme, '')
        self.assertEqual(parser.proxy_netloc, '')
        self.assertEqual(parser.getBodyStream().getvalue(), b'Hello.\n')

    def testComplexGET(self):
        data = b"""\
GET /foo/a+%2B%2F%C3%A4%3D%26a%3Aint?d=b+%2B%2F%3D%26b%3Aint&c+%2B%2F%3D%26c%3Aint=6 HTTP/8.4
FirstName: mickey
lastname: Mouse
content-length: 10

Hello mickey.
"""  # noqa: E501 line too long
        parser = self.parser
        self.feed(data)
        self.assertEqual(parser.command, 'GET')
        self.assertEqual(parser.version, '8.4')
        self.assertFalse(parser.empty)
        self.assertEqual(parser.headers,
                         {'FIRSTNAME': 'mickey',
                          'LASTNAME': 'Mouse',
                          'CONTENT_LENGTH': '10'})
        # path should be utf-8 encoded
        self.assertEqual(parser.path, '/foo/a++/ä=&a:int')
        self.assertEqual(parser.query,
                         'd=b+%2B%2F%3D%26b%3Aint&c+%2B%2F%3D%26c%3Aint=6')
        self.assertEqual(parser.getBodyStream().getvalue(), b'Hello mick')

    def testProxyGET(self):
        data = b"""\
GET https://example.com:8080/foobar HTTP/8.4
content-length: 7

Hello.
"""
        parser = self.parser
        self.feed(data)
        self.assertTrue(parser.completed)
        self.assertEqual(parser.version, '8.4')
        self.assertFalse(parser.empty)
        self.assertEqual(parser.headers,
                         {'CONTENT_LENGTH': '7'})
        self.assertEqual(parser.path, '/foobar')
        self.assertEqual(parser.command, 'GET')
        self.assertEqual(parser.proxy_scheme, 'https')
        self.assertEqual(parser.proxy_netloc, 'example.com:8080')
        self.assertEqual(parser.command, 'GET')
        self.assertEqual(parser.query, None)
        self.assertEqual(parser.getBodyStream().getvalue(), b'Hello.\n')

    def testDuplicateHeaders(self):
        # Ensure that headers with the same key get concatenated as per
        # RFC2616.
        data = b"""\
GET /foobar HTTP/8.4
x-forwarded-for: 10.11.12.13
x-forwarded-for: unknown,127.0.0.1
X-Forwarded_for: 255.255.255.255
content-length: 7

Hello.
"""
        self.feed(data)
        self.assertTrue(self.parser.completed)
        self.assertEqual(self.parser.headers, {
            'CONTENT_LENGTH': '7',
            'X_FORWARDED_FOR':
            '10.11.12.13, unknown,127.0.0.1, 255.255.255.255',
        })

    def testEmpty(self):
        data = b"""\


"""
        self.feed(data)
        self.assertTrue(self.parser.empty)

    def testParseHeader_Empty(self):
        self.parser.parse_header(b'')
        self.assertEqual({}, self.parser.headers)

    def testParseHeader_InvalidContentLength(self):
        data = b"""\
GET /foobar HTTP/1.0
Content-Length: Nope

        """
        self.feed(data)
        self.assertTrue(self.parser.completed)
        self.assertIsNone(self.parser.body_rcv)

    def test_get_header_lines_joins(self):
        self.parser.header = "header: abc\n\tdef"
        lines = self.parser.get_header_lines()
        self.assertEqual(lines, ['header: abcdef'])

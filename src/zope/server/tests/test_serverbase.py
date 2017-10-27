##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Tests for zope.server.serverbase
"""
import unittest

from zope.server.serverbase import ServerBase


class FakeSocket(object):
    data = b''

    def setblocking(self, _val):
        return None

    def fileno(self):
        return 42

    def getpeername(self):
        return ('localhost', 42)

    def listen(self, *args):
        pass

    def send(self, data):
        self.data += data
        return len(data)


class TestServerBase(unittest.TestCase):
    def test_ServerBase_ip_string_verbose(self):
        # Regression test for ServerBase

        # Bug: if the `ip` argument of ServerBase is a string
        # containing a numeric IP address, and the verbose argument
        # is enabled, ServerBase.__init__ would try to use self.logger
        # before it was initialized.

        # We will use a subclass of ServerBase so that unit tests do
        # not actually try to bind to ports.

        bound = []

        class ServerBaseForTest(ServerBase):
            def bind(self, addr):
                ip, port = addr
                bound.append("Listening on %s:%d" % (ip or '*', port))
        ServerBaseForTest('127.0.0.1', 80, start=False, verbose=True)
        self.assertEqual(bound,
                         ['Listening on 127.0.0.1:80'])

    def test_ServerBase_startup_logging(self):
        # Test for ServerBase verbose startup logging

        # We will use a subclass of ServerBase so that unit tests do
        # not actually try to bind to ports.

        logs = []

        class ServerBaseForTest(ServerBase):
            def bind(self, addr):
                self.socket = FakeSocket()

            def log_info(self, message, type='info'):
                logs.append(message.expandtabs())

        ServerBaseForTest('example.com', 80, start=True, verbose=True)
        self.assertEqual(logs[0],
                         "zope.server.serverbase started.\n"
                         "        Hostname: example.com\n"
                         "        Port: 80")

        # Subclasses can add extra information there

        class ServerForTest(ServerBaseForTest):
            def getExtraLogMessage(self):
                return '\n\tURL: http://example.com/'

        del logs[:]
        ServerForTest('example.com', 80, start=True, verbose=True)
        self.assertEqual(logs[0],
                         "zope.server.serverbase started.\n"
                         "        Hostname: example.com\n"
                         "        Port: 80\n"
                         "        URL: http://example.com/")

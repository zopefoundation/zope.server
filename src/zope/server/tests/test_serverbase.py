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

from zope.server import serverbase


class FakeSocket:
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

    def close(self):
        pass


class NonBindingServerBase(serverbase.ServerBase):

    def bind(self, addr):
        self.socket.close()
        self.socket = FakeSocket()

    logs = ()

    def log_info(self, message, type='info'):
        self.logs += (message.expandtabs(),)


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

        class ServerBaseForTest(NonBindingServerBase):
            def bind(self, addr):
                ip, port = addr
                bound.append("Listening on %s:%d" % (ip or '*', port))
        sb = ServerBaseForTest('127.0.0.1', 80, start=False, verbose=True)
        self.addCleanup(sb.close)
        self.assertEqual(bound,
                         ['Listening on 127.0.0.1:80'])

    def test_ServerBase_startup_logging(self):
        # Test for ServerBase verbose startup logging

        # We will use a subclass of ServerBase so that unit tests do
        # not actually try to bind to ports.

        sb = NonBindingServerBase('example.com', 80, start=True, verbose=True)
        self.addCleanup(sb.close)
        self.assertEqual(sb.logs[0],
                         "zope.server.serverbase started.\n"
                         "        Hostname: example.com\n"
                         "        Port: 80")

        # Subclasses can add extra information there

        class ServerForTest(NonBindingServerBase):
            def getExtraLogMessage(self):
                return '\n\tURL: http://example.com/'

        sb = ServerForTest('example.com', 80, start=True, verbose=True)
        self.addCleanup(sb.close)
        self.assertEqual(sb.logs[0],
                         "zope.server.serverbase started.\n"
                         "        Hostname: example.com\n"
                         "        Port: 80\n"
                         "        URL: http://example.com/")

    def test_computeServerName(self):
        sb = NonBindingServerBase('', 80, start=False)
        self.addCleanup(sb.close)

        self.assertNotEqual(sb.server_name, '')

    def test_computeServerName_errors(self):

        sb = NonBindingServerBase('', 80, start=False, verbose=True)
        self.addCleanup(sb.close)
        import socket

        class mysocket:
            error = socket.error

            def gethostname(self):
                return '127.0.0.1'

            def gethostbyaddr(self, name):
                raise OSError

        orig_socket = serverbase.socket
        serverbase.socket = mysocket()
        try:
            sb.logs = ()
            sb.computeServerName()
        finally:
            serverbase.socket = orig_socket

        self.assertEqual(sb.logs,
                         ('Computing hostname',
                          'Cannot do reverse lookup'))

    def test_addTask_no_dispatcher_executes_immediately(self):
        sb = NonBindingServerBase('', 80, start=False)
        self.addCleanup(sb.close)
        self.assertIsNone(sb.task_dispatcher)

        class Task:
            serviced = False

            def service(self):
                self.serviced = True

        task = Task()
        sb.addTask(task)
        self.assertTrue(task.serviced)

    def test_handle_accept_accept_returns_none(self):
        class SB(NonBindingServerBase):
            def accept(self):
                return None

        sb = SB('', 80, start=False)
        self.addCleanup(sb.close)
        self.assertIsNone(sb.handle_accept())

    def test_handle_accept_error(self):

        class SB(NonBindingServerBase):
            def accept(self):
                raise OSError()

        sb = SB('', 80, start=False)
        self.addCleanup(sb.close)
        self.assertIsNone(sb.handle_accept())

        self.assertEqual(sb.logs,
                         ('warning: server accept() threw an exception',))

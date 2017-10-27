##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""FTP Server tests
"""

import ftplib
import socket

import unittest

from io import BytesIO

from zope.server.adjustments import Adjustments
from zope.server.ftp.tests import demofs

from zope.server.tests import LoopTestMixin
from zope.server.tests.asyncerror import AsyncoreErrorHookMixin


my_adj = Adjustments()


def retrlines(ftpconn, cmd):
    res = []
    ftpconn.retrlines(cmd, res.append)
    return ''.join(res)


class TestIntegration(LoopTestMixin,
                      AsyncoreErrorHookMixin,
                      unittest.TestCase):

    task_dispatcher_count = 1

    def setUp(self):
        super(TestIntegration, self).setUp()
        # Avoid the tests hanging for a long time if something goes wrong
        socket.setdefaulttimeout(10) # XXX: We don't tear this down

    def _makeServer(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import FTPServer


        root_dir = demofs.Directory()
        root_dir['test'] = demofs.Directory()
        root_dir['test'].access['foo'] = 7
        root_dir['private'] = demofs.Directory()
        root_dir['private'].access['foo'] = 7
        root_dir['private'].access['anonymous'] = 0

        fs = demofs.DemoFileSystem(root_dir, 'foo')
        fs.writefile('/test/existing', BytesIO(b'test initial data'))
        fs.writefile('/private/existing', BytesIO(b'private initial data'))

        self.__fs = fs = demofs.DemoFileSystem(root_dir, 'root')
        fs.writefile('/existing', BytesIO(b'root initial data'))

        fs_access = demofs.DemoFileSystemAccess(root_dir, {'foo': 'bar'})

        return FTPServer(self.LOCALHOST, self.SERVER_PORT, fs_access,
                         task_dispatcher=self.td, adj=my_adj)


    def getFTPConnection(self, login=1):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        ftp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ftp.connect((self.LOCALHOST, self.port))
        result = ftp.recv(10000).split()[0]
        self.assertEqual(result, b'220')
        if login:
            ftp.send(b'USER foo\r\n')
            self.assertEqual(ftp.recv(1024).decode('ascii'),
                             status_messages['PASS_REQUIRED'] + '\r\n')
            ftp.send(b'PASS bar\r\n')
            self.assertEqual(ftp.recv(1024).decode('ascii'),
                             status_messages['LOGIN_SUCCESS'] + '\r\n')

        return ftp


    def execute(self, commands, login=1):
        ftp = self.getFTPConnection(login)

        try:
            if isinstance(commands, str):
                commands = (commands,)

            for command in commands:
                ftp.send(command.encode('ascii') + b'\r\n')
                result = ftp.recv(10000).decode('ascii')
            self.assertTrue(result.endswith('\r\n'))
        finally:
            ftp.close()
        return result


    def testABOR(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('ABOR', 1).rstrip(),
                         status_messages['TRANSFER_ABORTED'])


    def testAPPE(self):
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('foo', 'bar')
            fp = BytesIO(b'Charity never faileth')
            # Successful write
            conn.storbinary('APPE /test/existing', fp)
            self.assertEqual(self.__fs.files['test']['existing'].data,
                             b'test initial dataCharity never faileth')
        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()

    def testAPPE_errors(self):
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('foo', 'bar')

            fp = BytesIO(b'Speak softly')

            # Can't overwrite directory
            self.assertRaises(
                ftplib.error_perm, conn.storbinary, 'APPE /test', fp)

            # No such file
            self.assertRaises(
                ftplib.error_perm, conn.storbinary, 'APPE /nosush', fp)

            # No such dir
            self.assertRaises(
                ftplib.error_perm, conn.storbinary, 'APPE /nosush/f', fp)

            # Not allowed
            self.assertRaises(
                ftplib.error_perm, conn.storbinary, 'APPE /existing', fp)

        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()

    def testCDUP(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.execute('CWD test', 1)
        self.assertEqual(self.execute('CDUP', 1).rstrip(),
                         status_messages['SUCCESS_250'] %'CDUP')
        self.assertEqual(self.execute('CDUP', 1).rstrip(),
                         status_messages['SUCCESS_250'] %'CDUP')


    def testCWD(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('CWD test', 1).rstrip(),
                         status_messages['SUCCESS_250'] %'CWD')
        self.assertEqual(self.execute('CWD foo', 1).rstrip(),
                         status_messages['ERR_NO_DIR'] %'/foo')


    def testDELE(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('DELE test/existing', 1).rstrip(),
                         status_messages['SUCCESS_250'] %'DELE')
        res = self.execute('DELE bar', 1).split()[0]
        self.assertEqual(res, '550')
        self.assertEqual(self.execute('DELE', 1).rstrip(),
                         status_messages['ERR_ARGS'])


    def testHELP(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        result = status_messages['HELP_START'] + '\r\n'
        result += 'Help goes here somewhen.\r\n'
        result += status_messages['HELP_END'] + '\r\n'

        self.assertEqual(self.execute('HELP', 1), result)


    def testLIST(self):
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('anonymous', 'bar')
            self.assertRaises(ftplib.Error, retrlines, conn, 'LIST /foo')
            listing = retrlines(conn, 'LIST')
            self.assertGreater(len(listing), 0)
            listing = retrlines(conn, 'LIST -la')
            self.assertGreater(len(listing), 0)
        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()

    def testMKDLIST(self):
        self.execute(['MKD test/f1', 'MKD test/f2'], 1)
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('foo', 'bar')
            listing = []
            conn.retrlines('LIST /test', listing.append)
            self.assertGreaterEqual(len(listing), 2)
            listing = []
            conn.retrlines('LIST -lad test/f1', listing.append)
            self.assertEqual(len(listing), 1)
            self.assertEqual(listing[0][0], 'd')
        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()


    def testNOOP(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('NOOP', 0).rstrip(),
                         status_messages['SUCCESS_200'] %'NOOP')
        self.assertEqual(self.execute('NOOP', 1).rstrip(),
                         status_messages['SUCCESS_200'] %'NOOP')


    def testPASS(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('PASS', 0).rstrip(),
                         status_messages['LOGIN_MISMATCH'])
        self.execute('USER blah', 0)
        self.assertEqual(self.execute('PASS bar', 0).rstrip(),
                         status_messages['LOGIN_MISMATCH'])


    def testQUIT(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('QUIT', 0).rstrip(),
                         status_messages['GOODBYE'])
        self.assertEqual(self.execute('QUIT', 1).rstrip(),
                         status_messages['GOODBYE'])


    def testSTOR(self):
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('foo', 'bar')
            fp = BytesIO(b'Speak softly')
            # Can't overwrite directory
            self.assertRaises(
                ftplib.error_perm, conn.storbinary, 'STOR /test', fp)
            fp = BytesIO(b'Charity never faileth')
            # Successful write
            conn.storbinary('STOR /test/stuff', fp)
            self.assertEqual(self.__fs.files['test']['stuff'].data,
                             b'Charity never faileth')
        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()


    def testSTOR_over(self):
        conn = ftplib.FTP()
        try:
            conn.connect(self.LOCALHOST, self.port)
            conn.login('foo', 'bar')
            fp = BytesIO(b'Charity never faileth')
            conn.storbinary('STOR /test/existing', fp)
            self.assertEqual(self.__fs.files['test']['existing'].data,
                             b'Charity never faileth')
        finally:
            conn.close()
        # Make sure no garbage was left behind.
        self.testNOOP()


    def testUSER(self):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        self.assertEqual(self.execute('USER foo', 0).rstrip(),
                         status_messages['PASS_REQUIRED'])
        self.assertEqual(self.execute('USER', 0).rstrip(),
                         status_messages['ERR_ARGS'])

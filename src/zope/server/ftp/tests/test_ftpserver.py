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
import asyncore
import ftplib
import socket
import sys
import time
import traceback
import unittest
from threading import Thread, Event
from io import BytesIO

from zope.server.adjustments import Adjustments
from zope.server.ftp.tests import demofs
from zope.server.taskthreads import ThreadedTaskDispatcher
from zope.server.tests.asyncerror import AsyncoreErrorHook

td = ThreadedTaskDispatcher()

LOCALHOST = '127.0.0.1'
SERVER_PORT = 0      # Set these port numbers to 0 to auto-bind, or
CONNECT_TO_PORT = 0  # use specific numbers to inspect using TCPWatch.


my_adj = Adjustments()


def retrlines(ftpconn, cmd):
    res = []
    ftpconn.retrlines(cmd, res.append)
    return ''.join(res)


class Tests(AsyncoreErrorHook, unittest.TestCase):

    def setUp(self):
        super(Tests, self).setUp()
        # Avoid the tests hanging for a long time if something goes wrong
        socket.setdefaulttimeout(10)

        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import FTPServer
        td.setThreadCount(1)
        if len(asyncore.socket_map) != 1:
            # Let sockets die off.
            # TODO tests should be more careful to clear the socket map.
            asyncore.poll(0.1)  # pragma: no cover
        self.orig_map_size = len(asyncore.socket_map)

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

        self.server = FTPServer(LOCALHOST, SERVER_PORT, fs_access,
                                task_dispatcher=td, adj=my_adj)
        if CONNECT_TO_PORT == 0:
            self.port = self.server.socket.getsockname()[1]
        else: # pragma: no cover
            self.port = CONNECT_TO_PORT
        self.run_loop = 1
        self.counter = 0
        self.thread_started = Event()
        self.thread = Thread(target=self.loop)
        self.thread.setDaemon(True)
        self.thread.start()
        self.thread_started.wait(10.0)
        self.assertTrue(self.thread_started.isSet())

    def tearDown(self):
        self.run_loop = 0
        self.thread.join()
        td.shutdown()
        self.server.close()
        # Make sure all sockets get closed by asyncore normally.
        timeout = time.time() + 2
        while 1:
            if len(asyncore.socket_map) == self.orig_map_size:
                # Clean!
                break
            if time.time() >= timeout: # pragma: no cover
                self.fail('Leaked a socket: %s' % repr(asyncore.socket_map))
                break
            asyncore.poll(0.1) # pragma: no cover

        super(Tests, self).tearDown()

    def loop(self):
        self.thread_started.set()
        import select
        from errno import EBADF
        while self.run_loop:
            self.counter = self.counter + 1
            # Note that it isn't acceptable to fail out of
            # this loop. That will likely make the tests hang.
            try:
                asyncore.poll(0.1)
                continue
            except select.error as data: # pragma: no cover
                print("EXCEPTION POLLING IN LOOP(): %s" % data)
                if data.args[0] == EBADF:
                    for key in asyncore.socket_map:
                        print("")
                        try:
                            select.select([], [], [key], 0.0)
                        except select.error as v:
                            print("Bad entry in socket map %s %s" % (key, v))
                            print(asyncore.socket_map[key])
                            print(asyncore.socket_map[key].__class__)
                            del asyncore.socket_map[key]
                        else:
                            print("OK entry in socket map %s" % key)
                            print(asyncore.socket_map[key])
                            print(asyncore.socket_map[key].__class__)
                        print("")
            except: # pragma: no cover pylint:disable=bare-except
                print("WEIRD EXCEPTION IN LOOP")
                traceback.print_exception(*(sys.exc_info()+(100,)))
            print("")  # pragma: no cover

    def getFTPConnection(self, login=1):
        # import only now to prevent the testrunner from importing it too early
        # Otherwise dualmodechannel.the_trigger is closed by the ZEO tests
        from zope.server.ftp.server import status_messages
        ftp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ftp.connect((LOCALHOST, self.port))
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
            conn.connect(LOCALHOST, self.port)
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
            conn.connect(LOCALHOST, self.port)
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
            conn.connect(LOCALHOST, self.port)
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
            conn.connect(LOCALHOST, self.port)
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
            conn.connect(LOCALHOST, self.port)
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
            conn.connect(LOCALHOST, self.port)
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

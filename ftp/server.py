##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""FTP Server

$Id$
"""
import asyncore
import posixpath
import socket
from datetime import date, timedelta
from getopt import getopt, GetoptError

from zope.security.interfaces import Unauthorized
from zope.interface import implements
from zope.server.buffers import OverflowableBuffer
from zope.server.interfaces import ITask
from zope.server.interfaces.ftp import IFileSystemAccess
from zope.server.interfaces.ftp import IFTPCommandHandler
from zope.server.linereceiver.lineserverchannel import LineServerChannel
from zope.server.serverbase import ServerBase
from zope.server.dualmodechannel import DualModeChannel

status_messages = {
    'OPEN_DATA_CONN'   : '150 Opening %s mode data connection for file list',
    'OPEN_CONN'        : '150 Opening %s connection for %s',
    'SUCCESS_200'      : '200 %s command successful.',
    'TYPE_SET_OK'      : '200 Type set to %s.',
    'STRU_OK'          : '200 STRU F Ok.',
    'MODE_OK'          : '200 MODE S Ok.',
    'FILE_DATE'        : '213 %4d%02d%02d%02d%02d%02d',
    'FILE_SIZE'        : '213 %d Bytes',
    'HELP_START'       : '214-The following commands are recognized',
    'HELP_END'         : '214 Help done.',
    'SERVER_TYPE'      : '215 %s Type: %s',
    'SERVER_READY'     : '220 %s FTP server (Zope Async/Thread V0.1) ready.',
    'GOODBYE'          : '221 Goodbye.',
    'SUCCESS_226'      : '226 %s command successful.',
    'TRANS_SUCCESS'    : '226 Transfer successful.',
    'PASV_MODE_MSG'    : '227 Entering Passive Mode (%s,%d,%d)',
    'LOGIN_SUCCESS'    : '230 Login Successful.',
    'SUCCESS_250'      : '250 %s command successful.',
    'SUCCESS_257'      : '257 %s command successful.',
    'ALREADY_CURRENT'  : '257 "%s" is the current directory.',
    'PASS_REQUIRED'    : '331 Password required',
    'RESTART_TRANSFER' : '350 Restarting at %d. Send STORE or '
                         'RETRIEVE to initiate transfer.',
    'READY_FOR_DEST'   : '350 File exists, ready for destination.',
    'NO_DATA_CONN'     : "425 Can't build data connection",
    'TRANSFER_ABORTED' : '426 Connection closed; transfer aborted.',
    'CMD_UNKNOWN'      : "500 '%s': command not understood.",
    'INTERNAL_ERROR'   : "500 Internal error: %s",
    'ERR_ARGS'         : '500 Bad command arguments',
    'MODE_UNKOWN'      : '502 Unimplemented MODE type',
    'WRONG_BYTE_SIZE'  : '504 Byte size must be 8',
    'STRU_UNKNOWN'     : '504 Unimplemented STRU type',
    'NOT_AUTH'         : "530 You are not authorized to perform the "
                         "'%s' command",
    'LOGIN_REQUIRED'   : '530 Please log in with USER and PASS',
    'LOGIN_MISMATCH'   : '530 The username and password do not match.',
    'ERR_NO_LIST'      : '550 Could not list directory or file: %s',
    'ERR_NO_DIR'       : '550 "%s": No such directory.',
    'ERR_NO_FILE'      : '550 "%s": No such file.',
    'ERR_NO_DIR_FILE'  : '550 "%s": No such file or directory.',
    'ERR_IS_NOT_FILE'  : '550 "%s": Is not a file',
    'ERR_CREATE_FILE'  : '550 Error creating file.',
    'ERR_CREATE_DIR'   : '550 Error creating directory: %s',
    'ERR_DELETE_FILE'  : '550 Error deleting file: %s',
    'ERR_DELETE_DIR'   : '550 Error removing directory: %s',
    'ERR_OPEN_READ'    : '553 Could not open file for reading: %s',
    'ERR_OPEN_WRITE'   : '553 Could not open file for writing: %s',
    'ERR_IO'           : '553 I/O Error: %s',
    'ERR_RENAME'       : '560 Could not rename "%s" to "%s": %s',
    'ERR_RNFR_SOURCE'  : '560 No source filename specify. Call RNFR first.',
    }

class FTPServerChannel(LineServerChannel):
    """The FTP Server Channel represents a connection to a particular
       client. We can therefore store information here."""

    implements(IFTPCommandHandler)


    # List of commands that are always available
    special_commands = ('cmd_quit', 'cmd_type', 'cmd_noop', 'cmd_user',
                        'cmd_pass')

    # These are the commands that are accessing the filesystem.
    # Since this could be also potentially a longer process, these commands
    # are also the ones that are executed in a different thread.
    thread_commands = ('cmd_appe', 'cmd_cdup', 'cmd_cwd', 'cmd_dele',
                       'cmd_list', 'cmd_nlst', 'cmd_mdtm', 'cmd_mkd',
                       'cmd_pass', 'cmd_retr', 'cmd_rmd', 'cmd_rnfr',
                       'cmd_rnto', 'cmd_size', 'cmd_stor', 'cmd_stru')

    # Define the status messages
    status_messages = status_messages

    # Define the type of directory listing this server is returning
    system = ('UNIX', 'L8')

    # comply with (possibly troublesome) RFC959 requirements
    # This is necessary to correctly run an active data connection
    # through a firewall that triggers on the source port (expected
    # to be 'L-1', or 20 in the normal case).
    bind_local_minus_one = 0

    restart_position = 0

    type_map = {'a':'ASCII', 'i':'Binary', 'e':'EBCDIC', 'l':'Binary'}

    type_mode_map = {'a':'t', 'i':'b', 'e':'b', 'l':'b'}


    def __init__(self, server, conn, addr, adj=None):
        super(FTPServerChannel, self).__init__(server, conn, addr, adj)

        self.client_addr = (addr[0], 21)

        self.passive_acceptor = None
        self.client_dc = None

        self.transfer_mode = 'a'  # Have to default to ASCII :-|
        self.passive_mode = 0
        self.cwd = '/'
        self._rnfr = None

        self.username = ''
        self.credentials = None

        self.reply('SERVER_READY', self.server.server_name)


    def _getFileSystem(self):
        """Open the filesystem using the current credentials."""
        return self.server.fs_access.open(self.credentials)

    def cmd_abor(self, args):
        'See IFTPCommandHandler'
        if self.client_dc is not None:
            self.client_dc.close('TRANSFER_ABORTED')
        else:
            self.reply('TRANSFER_ABORTED')

    def cmd_appe (self, args):
        'See IFTPCommandHandler'
        return self.cmd_stor(args, 'a')


    def cmd_cdup(self, args):
        'See IFTPCommandHandler'
        path = self._generatePath('../')
        if self._getFileSystem().type(path):
            self.cwd = path
            self.reply('SUCCESS_250', 'CDUP')
        else:
            self.reply('ERR_NO_FILE', path)


    def cmd_cwd(self, args):
        'See IFTPCommandHandler'
        path = self._generatePath(args)
        if self._getFileSystem().type(path) == 'd':
            self.cwd = path
            self.reply('SUCCESS_250', 'CWD')
        else:
            self.reply('ERR_NO_DIR', path)


    def cmd_dele(self, args):
        'See IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)

        try:
            self._getFileSystem().remove(path)
        except OSError, err:
            self.reply('ERR_DELETE_FILE', str(err))
        else:
            self.reply('SUCCESS_250', 'DELE')


    def cmd_help(self, args):
        'See IFTPCommandHandler'
        self.reply('HELP_START')
        self.write('Help goes here somewhen.\r\n')
        self.reply('HELP_END')


    def cmd_list(self, args, long=1):
        'See IFTPCommandHandler'
        opts = ()
        if args.strip().startswith('-'):
            try:
                opts, args = getopt(args.split(), 'lad')
            except GetoptError:
                self.reply('ERR_ARGS')
                return

            if len(args) > 1:
                self.reply('ERR_ARGS')
                return

            args = args and args[0] or ''


        fs = self._getFileSystem()
        path = self._generatePath(args)
        if not fs.type(path):
            self.reply('ERR_NO_DIR_FILE', path)
            return
        args = args.split()
        try:
            s = self.getList(
                args, long,
                directory=bool([opt for opt in opts if opt[0]=='-d'])
                )
        except OSError, err:
            self.reply('ERR_NO_LIST', str(err))
            return
        ok_reply = ('OPEN_DATA_CONN', self.type_map[self.transfer_mode])
        cdc = XmitChannel(self, ok_reply)
        self.client_dc = cdc
        try:
            cdc.write(s)
            cdc.close_when_done()
        except OSError, err:
            cdc.close('ERR_NO_LIST', str(err))

    def getList(self, args, long=0, directory=0):
        # we need to scan the command line for arguments to '/bin/ls'...
        fs = self._getFileSystem()
        path_args = []
        for arg in args:
            if arg[0] != '-':
                path_args.append (arg)
            else:
                # ignore arguments
                pass
        if len(path_args) < 1:
            path = '.'
        else:
            path = path_args[0]

        path = self._generatePath(path)


        if fs.type(path) == 'd' and not directory:
            if long:
                file_list = map(ls, fs.ls(path))
            else:
                file_list = fs.names(path)
        else:
            if long:
                file_list = [ls(fs.lsinfo(path))]
            else:
                file_list = [posixpath.split(path)[1]]

        return '\r\n'.join(file_list) + '\r\n'



    def cmd_mdtm(self, args):
        'See IFTPCommandHandler'
        fs = self._getFileSystem()
        # We simply do not understand this non-standard extension to MDTM
        if len(args.split()) > 1:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        if not fs.type(path) == 'f':
            self.reply('ERR_IS_NOT_FILE', path)
        else:
            mtime = self._getFileSystem().mtime(path)
            if mtime is not None:
                mtime = (mtime.year, mtime.month, mtime.day,
                         mtime.hour, mtime. minute, mtime.second)
            else:
                mtime = 0, 0, 0, 0, 0, 0

            self.reply('FILE_DATE', mtime)


    def cmd_mkd(self, args):
        'See IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        try:
            self._getFileSystem().mkdir(path)
        except OSError, err:
            self.reply('ERR_CREATE_DIR', str(err))
        else:
            self.reply('SUCCESS_257', 'MKD')


    def cmd_mode(self, args):
        'See IFTPCommandHandler'
        if len(args) == 1 and args in 'sS':
            self.reply('MODE_OK')
        else:
            self.reply('MODE_UNKNOWN')


    def cmd_nlst(self, args):
        'See IFTPCommandHandler'
        self.cmd_list(args, 0)


    def cmd_noop(self, args):
        'See IFTPCommandHandler'
        self.reply('SUCCESS_200', 'NOOP')


    def cmd_pass(self, args):
        'See IFTPCommandHandler'
        self.authenticated = 0
        password = args
        credentials = (self.username, password)
        try:
            self.server.fs_access.authenticate(credentials)
        except Unauthorized:
            self.reply('LOGIN_MISMATCH')
            self.close_when_done()
        else:
            self.credentials = credentials
            self.authenticated = 1
            self.reply('LOGIN_SUCCESS')


    def cmd_pasv(self, args):
        'See IFTPCommandHandler'
        pc = self.newPassiveAcceptor()
        self.client_dc = None
        port = pc.addr[1]
        ip_addr = pc.control_channel.getsockname()[0]
        self.reply('PASV_MODE_MSG', (','.join(ip_addr.split('.')),
                                     port/256,
                                     port%256 ) )


    def cmd_port(self, args):
        'See IFTPCommandHandler'
        info = args.split(',')
        ip = '.'.join(info[:4])
        port = int(info[4])*256 + int(info[5])
        # how many data connections at a time?
        # I'm assuming one for now...
        # TODO: we should (optionally) verify that the
        # ip number belongs to the client.  [wu-ftpd does this?]
        self.client_addr = (ip, port)
        self.reply('SUCCESS_200', 'PORT')


    def cmd_pwd(self, args):
        'See IFTPCommandHandler'
        self.reply('ALREADY_CURRENT', self.cwd)


    def cmd_quit(self, args):
        'See IFTPCommandHandler'
        self.reply('GOODBYE')
        self.close_when_done()


    def cmd_retr(self, args):
        'See IFTPCommandHandler'
        fs = self._getFileSystem()
        if not args:
            self.reply('CMD_UNKNOWN', 'RETR')
        path = self._generatePath(args)

        if not (fs.type(path) == 'f'):
            self.reply('ERR_IS_NOT_FILE', path)
            return

        start = 0
        if self.restart_position:
            start = self.restart_position
            self.restart_position = 0

        ok_reply = 'OPEN_CONN', (self.type_map[self.transfer_mode], path)
        cdc = XmitChannel(self, ok_reply)
        self.client_dc = cdc
        outstream = ApplicationXmitStream(cdc)

        try:
            fs.readfile(path, outstream, start)
            cdc.close_when_done()
        except OSError, err:
            cdc.close('ERR_OPEN_READ', str(err))
        except IOError, err:
            cdc.close('ERR_IO', str(err))


    def cmd_rest(self, args):
        'See IFTPCommandHandler'
        try:
            pos = int(args)
        except ValueError:
            self.reply('ERR_ARGS')
            return
        self.restart_position = pos
        self.reply('RESTART_TRANSFER', pos)


    def cmd_rmd(self, args):
        'See IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        try:
            self._getFileSystem().rmdir(path)
        except OSError, err:
            self.reply('ERR_DELETE_DIR', str(err))
        else:
            self.reply('SUCCESS_250', 'RMD')


    def cmd_rnfr(self, args):
        'See IFTPCommandHandler'
        path = self._generatePath(args)
        if self._getFileSystem().type(path):
            self._rnfr = path
            self.reply('READY_FOR_DEST')
        else:
            self.reply('ERR_NO_FILE', path)


    def cmd_rnto(self, args):
        'See IFTPCommandHandler'
        path = self._generatePath(args)
        if self._rnfr is None:
            self.reply('ERR_RENAME')
        try:
            self._getFileSystem().rename(self._rnfr, path)
        except OSError, err:
            self.reply('ERR_RENAME', (self._rnfr, path, str(err)))
        else:
            self.reply('SUCCESS_250', 'RNTO')
        self._rnfr = None


    def cmd_size(self, args):
        'See IFTPCommandHandler'
        path = self._generatePath(args)
        fs = self._getFileSystem()
        if not (fs.type(path) == 'f'):
            self.reply('ERR_NO_FILE', path)
        else:
            self.reply('FILE_SIZE', fs.size(path))


    def cmd_stor(self, args, write_mode='w'):
        'See IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)

        start = 0
        if self.restart_position:
            self.start = self.restart_position
        mode = write_mode + self.type_mode_map[self.transfer_mode]

        if not self._getFileSystem().writable(path):
            self.reply('ERR_OPEN_WRITE', "Can't write file")
            return

        cdc = RecvChannel(self, (path, mode, start))
        self.client_dc = cdc
        self.reply('OPEN_CONN', (self.type_map[self.transfer_mode], path))
        self.connectDataChannel(cdc)


    def finishedRecv(self, buffer, (path, mode, start)):
        """Called by RecvChannel when the transfer is finished."""
        # Always called in a task.
        try:
            infile = buffer.getfile()
            infile.seek(0)
            self._getFileSystem().writefile(path, infile, start,
                                            append=(mode[0]=='a'))
        except OSError, err:
            self.reply('ERR_OPEN_WRITE', str(err))
        except IOError, err:
            self.reply('ERR_IO', str(err))
        except:
            self.exception()
        else:
            self.reply('TRANS_SUCCESS')


    def cmd_stru(self, args):
        'See IFTPCommandHandler'
        if len(args) == 1 and args in 'fF':
            self.reply('STRU_OK')
        else:
            self.reply('STRU_UNKNOWN')


    def cmd_syst(self, args):
        'See IFTPCommandHandler'
        self.reply('SERVER_TYPE', self.system)


    def cmd_type(self, args):
        'See IFTPCommandHandler'
        # ascii, ebcdic, image, local <byte size>
        args = args.split()
        t = args[0].lower()
        # no support for EBCDIC
        # if t not in ['a','e','i','l']:
        if t not in ['a','i','l']:
            self.reply('ERR_ARGS')

        elif t == 'l' and (len(args) > 2 and args[2] != '8'):
            self.reply('WRONG_BYTE_SIZE')

        else:
            self.transfer_mode = t
            self.reply('TYPE_SET_OK', self.type_map[t])


    def cmd_user(self, args):
        'See IFTPCommandHandler'
        self.authenticated = 0
        if len(args) > 1:
            self.username = args
            self.reply('PASS_REQUIRED')
        else:
            self.reply('ERR_ARGS')

    #
    ############################################################

    def _generatePath(self, args):
        """Convert relative paths to absolute paths."""
        # We use posixpath even on non-Posix platforms because we don't want
        # slashes converted to backslashes.
        path = posixpath.join(self.cwd, args)
        return posixpath.normpath(path)


    def newPassiveAcceptor(self):
        # ensure that only one of these exists at a time.
        if self.passive_acceptor is not None:
            self.passive_acceptor.close()
            self.passive_acceptor = None
        self.passive_acceptor = PassiveAcceptor(self)
        return self.passive_acceptor



    def connectDataChannel(self, cdc):
        pa = self.passive_acceptor
        if pa:
            # PASV mode.
            if pa.ready:
                # a connection has already been made.
                conn, addr = pa.ready
                cdc.set_socket (conn)
                cdc.connected = 1
                self.passive_acceptor.close()
                self.passive_acceptor = None
            # else we're still waiting for a connect to the PASV port.
            # FTP Explorer is known to do this.
        else:
            # not in PASV mode.
            ip, port = self.client_addr
            cdc.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.bind_local_minus_one:
                cdc.bind(('', self.server.port - 1))
            try:
                cdc.connect((ip, port))
            except socket.error:
                cdc.close('NO_DATA_CONN')

                
    def notifyClientDCClosing(self, *reply_args):
        if self.client_dc is not None:
            self.client_dc = None
            if reply_args:
                self.reply(*reply_args)


    def close(self):
        LineServerChannel.close(self)
        # Make sure the client DC gets closed too.
        cdc = self.client_dc
        if cdc is not None:
            self.client_dc = None
            cdc.close()




def ls(ls_info):
    """Formats a directory entry similarly to the 'ls' command.
    """

    info = {
        'owner_name': 'na',
        'owner_readable': True,
        'owner_writable': True,
        'group_name': "na",
        'group_readable': True,
        'group_writable': True,
        'other_readable': False,
        'other_writable': False,
        'nlinks': 1,
        'size': 0,
        }

    if ls_info['type'] == 'd':
        info['owner_executable'] = True
        info['group_executable'] = True
        info['other_executable'] = True
    else:
        info['owner_executable'] = False
        info['group_executable'] = False
        info['other_executable'] = False

    info.update(ls_info)

    mtime = info.get('mtime')
    if mtime is not None:
        if date.today() - mtime.date() > timedelta(days=180):
            mtime = mtime.strftime('%b %d  %Y')
        else:
            mtime = mtime.strftime('%b %d %H:%M')
    else:
        mtime = "Jan 02  0000"

    return "%s%s%s%s%s%s%s%s%s%s %3d %-8s %-8s %8d %s %s" % (
        info['type'] == 'd' and 'd' or '-',
        info['owner_readable'] and 'r' or '-',
        info['owner_writable'] and 'w' or '-',
        info['owner_executable'] and 'x' or '-',
        info['group_readable'] and 'r' or '-',
        info['group_writable'] and 'w' or '-',
        info['group_executable'] and 'x' or '-',
        info['other_readable'] and 'r' or '-',
        info['other_writable'] and 'w' or '-',
        info['other_executable'] and 'x' or '-',
        info['nlinks'],
        info['owner_name'],
        info['group_name'],
        info['size'],
        mtime,
        info['name'],
        )


class PassiveAcceptor(asyncore.dispatcher):
    """This socket accepts a data connection, used when the server has
       been placed in passive mode.  Although the RFC implies that we
       ought to be able to use the same acceptor over and over again,
       this presents a problem: how do we shut it off, so that we are
       accepting connections only when we expect them?  [we can't]

       wuftpd, and probably all the other servers, solve this by
       allowing only one connection to hit this acceptor.  They then
       close it.  Any subsequent data-connection command will then try
       for the default port on the client side [which is of course
       never there].  So the 'always-send-PORT/PASV' behavior seems
       required.

       Another note: wuftpd will also be listening on the channel as
       soon as the PASV command is sent.  It does not wait for a data
       command first.

       --- we need to queue up a particular behavior:
       1) xmit : queue up producer[s]
       2) recv : the file object

       It would be nice if we could make both channels the same.
       Hmmm.."""

    ready = None

    def __init__ (self, control_channel):
        asyncore.dispatcher.__init__ (self)
        self.control_channel = control_channel
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to an address on the interface that the
        # control connection is coming from.
        self.bind((self.control_channel.getsockname()[0], 0))
        self.addr = self.getsockname()
        self.listen(1)


    def log (self, *ignore):
        pass


    def handle_accept (self):
        conn, addr = self.accept()
        conn.setblocking(0)
        dc = self.control_channel.client_dc
        if dc is not None:
            dc.set_socket(conn)
            dc.addr = addr
            dc.connected = 1
            self.control_channel.passive_acceptor = None
        else:
            self.ready = conn, addr
        self.close()


class RecvChannel(DualModeChannel):
    """ """

    complete_transfer = 0
    _fileno = None  # provide a default for asyncore.dispatcher._fileno

    def __init__ (self, control_channel, finish_args):
        self.control_channel = control_channel
        self.finish_args = finish_args
        self.inbuf = OverflowableBuffer(control_channel.adj.inbuf_overflow)
        DualModeChannel.__init__(self, None, None, control_channel.adj)
        # Note that this channel starts out in async mode.

    def writable (self):
        return 0

    def handle_connect (self):
        pass

    def received (self, data):
        if data:
            self.inbuf.append(data)

    def handle_close (self):
        """Client closed, indicating EOF."""
        c = self.control_channel
        task = FinishedRecvTask(c, self.inbuf, self.finish_args)
        self.complete_transfer = 1
        self.close()
        c.start_task(task)

    def close(self, *reply_args):
        try:
            c = self.control_channel
            if c is not None:
                self.control_channel = None
                if not self.complete_transfer and not reply_args:
                    # Not all data transferred
                    reply_args = ('TRANSFER_ABORTED',)
                c.notifyClientDCClosing(*reply_args)
        finally:
            if self.socket is not None:
                # XXX asyncore.dispatcher.close() doesn't like socket == None
                DualModeChannel.close(self)



class FinishedRecvTask(object):

    implements(ITask)

    def __init__(self, control_channel, inbuf, finish_args):
        self.control_channel = control_channel
        self.inbuf = inbuf
        self.finish_args = finish_args

    def service(self):
        """Called to execute the task.
        """
        close_on_finish = 0
        c = self.control_channel
        try:
            try:
                c.finishedRecv(self.inbuf, self.finish_args)
            except socket.error:
                close_on_finish = 1
                if c.adj.log_socket_errors:
                    raise
        finally:
            c.end_task(close_on_finish)


    def cancel(self):
        'See ITask'
        self.control_channel.close_when_done()


    def defer(self):
        'See ITask'
        pass


class XmitChannel(DualModeChannel):

    opened = 0
    _fileno = None  # provide a default for asyncore.dispatcher._fileno

    def __init__ (self, control_channel, ok_reply_args):
        self.control_channel = control_channel
        self.ok_reply_args = ok_reply_args
        self.set_sync()
        DualModeChannel.__init__(self, None, None, control_channel.adj)

    def _open(self):
        """Signal the client to open the connection."""
        self.opened = 1
        self.control_channel.reply(*self.ok_reply_args)
        self.control_channel.connectDataChannel(self)

    def write(self, data):
        if self.control_channel is None:
            raise IOError, 'Client FTP connection closed'
        if not self.opened:
            self._open()
        DualModeChannel.write(self, data)

    def readable(self):
        return not self.connected

    def handle_read(self):
        # This is only called when making the connection.
        try:
            self.recv(1)
        except:
            # The connection failed.
            self.close('NO_DATA_CONN')

    def handle_connect(self):
        pass

    def handle_comm_error(self):
        self.close('TRANSFER_ABORTED')

    def close(self, *reply_args):
        try:
            c = self.control_channel
            if c is not None:
                self.control_channel = None
                if not reply_args:
                    if not len(self.outbuf):
                        # All data transferred
                        if not self.opened:
                            # Zero-length file
                            self._open()
                        reply_args = ('TRANS_SUCCESS',)
                    else:
                        # Not all data transferred
                        reply_args = ('TRANSFER_ABORTED',)
                c.notifyClientDCClosing(*reply_args)
        finally:
            if self.socket is not None:
                # XXX asyncore.dispatcher.close() doesn't like socket == None
                DualModeChannel.close(self)


class ApplicationXmitStream(object):
    """Provide stream output, remapping close() to close_when_done().
    """

    def __init__(self, xmit_channel):
        self.write = xmit_channel.write
        self.flush = xmit_channel.flush
        self.close = xmit_channel.close_when_done


class FTPServer(ServerBase):
    """Generic FTP Server"""

    channel_class = FTPServerChannel
    SERVER_IDENT = 'zope.server.ftp'


    def __init__(self, ip, port, fs_access, *args, **kw):

        assert IFileSystemAccess.providedBy(fs_access)
        self.fs_access = fs_access

        super(FTPServer, self).__init__(ip, port, *args, **kw)

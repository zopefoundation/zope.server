##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id: ftpstatusmessages.py,v 1.2 2002/12/25 14:15:23 jim Exp $
"""


status_msgs = {
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

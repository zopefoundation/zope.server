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
"""OS-Emulator Package

Simulates OS-level directory listing output for *nix and MS-DOS (including
Windows NT).

$Id: osemulators.py,v 1.3 2003/01/30 16:01:09 jim Exp $
"""

import stat
import datetime

mode_table = {
        '0':'---',
        '1':'--x',
        '2':'-w-',
        '3':'-wx',
        '4':'r--',
        '5':'r-x',
        '6':'rw-',
        '7':'rwx'
        }


def ls_longify((filename, stat_info)):
    """Formats a directory entry similarly to the 'ls' command.
    """

    # Note that we expect a little deviance from the result of os.stat():
    # we expect the ST_UID and ST_GID fields to contain user IDs.
    username = str(stat_info[stat.ST_UID])[:8]
    grpname = str(stat_info[stat.ST_GID])[:8]

    mode_octal = ('%o' % stat_info[stat.ST_MODE])[-3:]
    mode = ''.join(map(mode_table.get, mode_octal))
    if stat.S_ISDIR (stat_info[stat.ST_MODE]):
        dirchar = 'd'
    else:
        dirchar = '-'
    date = ls_date(datetime.datetime.now(), stat_info[stat.ST_MTIME])

    return '%s%s %3d %-8s %-8s %8d %s %s' % (
            dirchar,
            mode,
            stat_info[stat.ST_NLINK],
            username,
            grpname,
            stat_info[stat.ST_SIZE],
            date,
            filename
            )


def ls_date(now, t):
    """Emulate the 'ls' command's date field.  It has two formats.
       If the date is more than 180 days in the past or future, then
       it's like this:
         Oct 19  1995
       otherwise, it looks like this:
         Oct 19 17:33

    """
    if now.date() - t.date() > datetime.timedelta(days=180):
        return t.strftime('%b %d %Y')
    else:
        return t.strftime('%b %d %H:%M')


def msdos_longify((file, stat_info)):
    """This matches the output of NT's ftp server (when in MSDOS mode)
       exactly.
    """
    if stat.S_ISDIR(stat_info[stat.ST_MODE]):
        dir = '<DIR>'
    else:
        dir = '     '
    date = msdos_date(stat_info[stat.ST_MTIME])
    return '%s       %s %8d %s' % (date, dir, stat_info[stat.ST_SIZE], file)


def msdos_date(t):
    """Emulate MS-DOS 'dir' command. Example:
         09-19-95 05:33PM
    """
    return t.strftime('%m-%d-%y %H:%M%p')

##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""XXX short summary goes here.

XXX longer description goes here.

$Id: test_osemulators.py,v 1.1 2003/01/30 16:01:11 jim Exp $
"""

from unittest import TestCase, TestSuite, main, makeSuite
from datetime import datetime, timedelta, tzinfo
from zope.server.ftp.osemulators import ls_date

class tzinfo(tzinfo):
    def utcoffset(self, dt):
        return 300
    def dst(self, dt):
        pass
    def tsname(self, dt):
        pass

class Test(TestCase):

    def test_ls_date(self):
        # test recent dates
        now = datetime(2003, 1, 27, 15, 56, 37)
        t = now - timedelta(hours=1, minutes=23, seconds=14,
                            milliseconds=123)
        t = t.replace(tzinfo = tzinfo())

        self.assertEqual(ls_date(now, t), 'Jan 27 14:33')

        # test less recent dates
        t = t - timedelta(days=175, hours=1, minutes=23, seconds=14,
                          milliseconds=123)
        self.assertEqual(ls_date(now, t), 'Aug 05 13:10')

        # test non recent dates
        t = t - timedelta(days=10, hours=1, minutes=23, seconds=14,
                          milliseconds=123)
        self.assertEqual(ls_date(now, t), 'Jul 26 2002')

        # test really old dates
        t = t - timedelta(days=20000, hours=1, minutes=23, seconds=14,
                          milliseconds=123)
        self.assertEqual(ls_date(now, t), 'Oct 23 1947')
    

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')

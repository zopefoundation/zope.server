##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

$Id$
"""

import unittest
import logging


class TestCommonHitLogger(unittest.TestCase):

    def test_default_constructor(self):
        from zope.server.http.commonhitlogger import CommonHitLogger
        from zope.server.logger.unresolvinglogger import UnresolvingLogger
        from zope.server.logger.pythonlogger import PythonLogger
        logger = CommonHitLogger()
        # CommonHitLogger is registered as an argumentless factory via
        # ZCML, so the defaults should be sensible
        self.assert_(isinstance(logger.output, UnresolvingLogger))
        self.assert_(isinstance(logger.output.logger, PythonLogger))
        self.assert_(logger.output.logger.name, 'hitlog')
        self.assert_(logger.output.logger.level, logging.INFO)

    # XXX please add unit tests for other methods as well:
    #     compute_timezone_for_log
    #     log_date_string
    #     log


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCommonHitLogger))
    return suite


if __name__ == '__main__':
    unittest.main()

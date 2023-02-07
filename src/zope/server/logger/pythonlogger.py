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
"""Proxy between the server's and Python's logger interfaces.
"""
import logging

from zope.interface import implementer

from zope.server.interfaces.logger import IMessageLogger
from zope.server.interfaces.logger import IRequestLogger


@implementer(IMessageLogger, IRequestLogger)
class PythonLogger:
    """Proxy for Python's logging module"""

    def __init__(self, name=None, level=logging.INFO):
        """
        :keyword str name: The name of a logger to use,
           or the logger itself.
        """
        name = getattr(name, 'name', name)
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)

    def __repr__(self):
        return '<python logger: {} {}>'.format(
            self.name, logging.getLevelName(self.level))

    def logMessage(self, message):
        """See IMessageLogger"""
        self.logger.log(self.level, message.rstrip())

    def logRequest(self, ip, message):
        """
        Log request is implemented to call :meth:`logMessage` without
        attempting any resolution.
        """
        self.logMessage('{}{}'.format(ip, message))

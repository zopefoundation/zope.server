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

$Id: resolvinglogger.py,v 1.2 2002/12/25 14:15:27 jim Exp $
"""
from zope.server.interfaces.logger import IRequestLogger


class ResolvingLogger:
    """Feed (ip, message) combinations into this logger to get a
    resolved hostname in front of the message.  The message will not
    be logged until the PTR request finishes (or fails)."""

    __implements__ = IRequestLogger

    def __init__(self, resolver, logger):
        self.resolver = resolver
        # logger is an IMessageLogger
        self.logger = logger


    class logger_thunk:
        def __init__(self, message, logger):
            self.message = message
            self.logger = logger

        def __call__(self, host, ttl, answer):
            if not answer:
                answer = host
            self.logger.logMessage('%s: %s' % (answer, self.message))

    def logRequest(self, ip, message):
        'See IRequestLogger'
        self.resolver.resolve_ptr(
                ip,
                self.logger_thunk(
                        message,
                        self.logger
                        )
                )
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
"""Common Access Logger
"""

import time

from zope.server.http.http_date import monthname
from zope.server.logger.pythonlogger import PythonLogger
from zope.server.logger.resolvinglogger import ResolvingLogger


class CommonAccessLogger:
    """Output accesses in common HTTP log format."""

    def __init__(self, logger_object='accesslog', resolver=None):
        """

        :keyword logger_object: Either a Python :class:`logging.Logger`
           object, or a string giving the name of a Python logger to find.

        .. versionchanged:: 4.0.0
           Remove support for arbitrary ``IMessageLogger`` objects in
           *logger_object*. Logging is now always directed through the
           Python standard logging library.
        """
        self.output = PythonLogger(logger_object)

        # self.output is an IRequestLogger, which PythonLogger implements
        # as unresolving.
        if resolver is not None:
            self.output = ResolvingLogger(resolver, self.output)

    @classmethod
    def compute_timezone_for_log(cls, tz):
        if tz > 0:
            neg = 1
        else:
            neg = 0
            tz = -tz
        h, rem = divmod(tz, 3600)
        m, rem = divmod(rem, 60)
        if neg:
            return '-%02d%02d' % (h, m)
        return '+%02d%02d' % (h, m)

    tz_for_log = None
    tz_for_log_alt = None

    _localtime = staticmethod(time.localtime)

    def log_date_string(self, when):
        logtime = self._localtime(when)
        Y, M, D, h, m, s = logtime[:6]

        if not time.daylight:
            tz = self.tz_for_log
            if tz is None:
                tz = self.compute_timezone_for_log(time.timezone)
                self.tz_for_log = tz
        else:
            tz = self.tz_for_log_alt
            if tz is None:
                tz = self.compute_timezone_for_log(time.altzone)
                self.tz_for_log_alt = tz

        return '%d/%s/%02d:%02d:%02d:%02d %s' % (
            D, monthname[M], Y, h, m, s, tz)

    def log(self, task):
        """Receive a completed task and logs it in the common log format."""
        now = time.time()
        request_data = task.request_data
        req_headers = request_data.headers

        user_name = task.auth_user_name or 'anonymous'
        user_agent = req_headers.get('USER_AGENT', '')
        referer = req_headers.get('REFERER', '')

        self.output.logRequest(
            task.channel.addr[0],
            ' - %s [%s] "%s" %s %d "%s" "%s"\n' % (
                user_name,
                self.log_date_string(now),
                request_data.first_line,
                task.status,
                task.bytes_written,
                referer,
                user_agent
            )
        )

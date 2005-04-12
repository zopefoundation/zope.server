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
"""WSGI-compliant HTTP Server that uses the Zope Publisher for executing a task.

$Id: publisherhttpserver.py 29535 2005-03-17 22:44:37Z garrett $
"""
import re
import sys
from zope.server.http.httpserver import HTTPServer
from zope.publisher.publish import publish


class WSGIHTTPServer(HTTPServer):
    """Zope Publisher-specific WSGI-compliant HTTP Server"""

    def __init__(self, application, sub_protocol=None, *args, **kw):

        if sys.platform[:3] == "win" and args[0] == 'localhost':
            args = ('',) + args[1:]

        self.application = application

        if sub_protocol:
            self.SERVER_IDENT += ' (%s)' %str(sub_protocol)

        HTTPServer.__init__(self, *args, **kw)


    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        env['wsgi.input'] = task.request_data.getBodyStream()

        def start_response(status, headers):
            # Prepare the headers for output
            status, reason = re.match('([0-9]*) (.*)', status).groups()
            task.setResponseStatus(status, reason)
            task.appendResponseHeaders(['%s: %s' % i for i in headers])

            # Return the write method used to write the response data.
            return task.write

        # Call the application to handle the request and write a response
        self.application(env, start_response)

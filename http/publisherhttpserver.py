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

$Id: publisherhttpserver.py,v 1.2 2002/12/25 14:15:24 jim Exp $
"""

from zope.server.http.httpserver import HTTPServer
from zope.publisher.publish import publish


class PublisherHTTPServer(HTTPServer):
    """Zope Publisher-specific HTTP Server"""

    __implements__ = HTTPServer.__implements__

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):
        sub_protocol = str(sub_protocol)

        self.request_factory = request_factory

        # An HTTP server is not limited to server up HTML; it can be
        # used for other protocols, like XML-RPC, SOAP and so as well
        # Here we just allow the logger to output the sub-protocol type.
        if sub_protocol:
            self.SERVER_IDENT += ' (%s)' %sub_protocol

        HTTPServer.__init__(self, *args, **kw)

    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        instream = task.request_data.getBodyStream()

        request = self.request_factory(instream, task, env)
        response = request.response
        response.setHeaderOutput(task)
        publish(request)
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
"""HTTP Server that uses the Zope Publisher for executing a task.

$Id$
"""
from zope.server.http.httpserver import HTTPServer
from zope.publisher.publish import publish


class PublisherHTTPServer(HTTPServer):
    """Zope Publisher-specific HTTP Server"""

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):

        # The common HTTP
        self.request_factory = request_factory

        # An HTTP server is not limited to serving up HTML; it can be
        # used for other protocols, like XML-RPC, SOAP and so as well
        # Here we just allow the logger to output the sub-protocol type.
        if sub_protocol:
            self.SERVER_IDENT += ' (%s)' %str(sub_protocol)

        HTTPServer.__init__(self, *args, **kw)

    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        instream = task.request_data.getBodyStream()

        request = self.request_factory(instream, task, env)
        response = request.response
        response.setHeaderOutput(task)
        response.setHTTPTransaction(task)
        publish(request)


class PMDBHTTPServer(PublisherHTTPServer):
    """Enter the post-mortem debugger when there's an error"""

    def executeRequest(self, task):
        """Overrides HTTPServer.executeRequest()."""
        env = task.getCGIEnvironment()
        instream = task.request_data.getBodyStream()

        request = self.request_factory(instream, task, env)
        response = request.response
        response.setHeaderOutput(task)
        try:
            publish(request, handle_errors=False)
        except:
            import sys, pdb
            print "%s:" % sys.exc_info()[0]
            print sys.exc_info()[1]
            pdb.post_mortem(sys.exc_info()[2])
            raise


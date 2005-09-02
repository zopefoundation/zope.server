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
import zope.deprecation
from zope.server.http import wsgihttpserver
from zope.publisher.publish import publish
import zope.security.management


class PublisherHTTPServer(wsgihttpserver.WSGIHTTPServer):

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):

        def application(environ, start_response):
            request = request_factory(environ['wsgi.input'], environ)
            response = request.response
            publish(request)
            start_response(response.getStatusString(), response.getHeaders())
            return response.result.body

        return super(PublisherHTTPServer, self).__init__(
            application, sub_protocol, *args, **kw)


class PMDBHTTPServer(wsgihttpserver.WSGIHTTPServer):

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):

        def application(environ, start_response):
            request = request_factory(environ['wsgi.input'], environ)
            response = request.response
            try:
                publish(request, handle_errors=False)
            except:
                import sys, pdb
                print "%s:" % sys.exc_info()[0]
                print sys.exc_info()[1]
                zope.security.management.restoreInteraction()
                try:
                    pdb.post_mortem(sys.exc_info()[2])
                    raise
                finally:
                    zope.security.management.endInteraction()
            start_response(response.getStatusString(), response.getHeaders())
            return response.result.body

        return super(PublisherHTTPServer, self).__init__(
            application, sub_protocol, *args, **kw)

zope.deprecation.deprecated(
    ('PublisherHTTPServer', 'PMDBHTTPServer'),
    'This plain publisher support has been replaced in favor of the '
    'WSGI HTTP server '
    'The reference will be gone in X3.4.')

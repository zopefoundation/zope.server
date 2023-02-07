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
"""HTTP Server that uses the Zope Publisher for executing a task.
"""
import sys

from zope.publisher.publish import publish as _publish

from zope.server.http import wsgihttpserver


def _make_application(request_factory, publish):
    def application(environ, start_response):
        request = request_factory(environ['wsgi.input'], environ)
        request = publish(request)
        response = request.response
        start_response(response.getStatusString(), response.getHeaders())
        return response.consumeBody()
    return application


class PublisherHTTPServer(wsgihttpserver.WSGIHTTPServer):

    def __init__(self, request_factory, sub_protocol=None, *args, **kw):

        super().__init__(
            self._make_application(request_factory), sub_protocol, *args, **kw)

    @classmethod
    def _make_application(cls, request_factory, publish=_publish):
        return _make_application(request_factory, publish)


def _pmdb_publish(request):
    try:
        return _publish(request, handle_errors=False)
    except:  # noqa: E722 pylint:disable=bare-except
        wsgihttpserver.PMDBWSGIHTTPServer.post_mortem(sys.exc_info())


class PMDBHTTPServer(PublisherHTTPServer):

    @classmethod
    def _make_application(cls, request_factory, publish=_pmdb_publish):
        return super()._make_application(
            request_factory, publish)

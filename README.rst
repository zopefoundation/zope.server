
.. image:: https://img.shields.io/pypi/v/zope.server.svg
        :target: https://pypi.python.org/pypi/zope.server/
        :alt: Latest release

.. image:: https://img.shields.io/pypi/pyversions/zope.server.svg
        :target: https://pypi.org/project/zope.server/
        :alt: Supported Python versions

.. image:: https://github.com/zopefoundation/zope.server/actions/workflows/tests.yml/badge.svg
        :target: https://github.com/zopefoundation/zope.server/actions/workflows/tests.yml

.. image:: https://coveralls.io/repos/github/zopefoundation/zope.server/badge.svg?branch=master
        :target: https://coveralls.io/github/zopefoundation/zope.server?branch=master

This package contains generic base classes for channel-based servers, the
servers themselves and helper objects, such as tasks and requests.

============
WSGI Support
============

`zope.server`'s HTTP server comes with WSGI_ support.
``zope.server.http.wsgihttpserver.WSGIHTTPServer`` can act as a WSGI gateway.
There's also an entry point for PasteDeploy_ that lets you use zope.server's
WSGI gateway from a configuration file, e.g.::

  [server:main]
  use = egg:zope.server
  host = 127.0.0.1
  port = 8080

.. _WSGI: http://www.python.org/dev/peps/pep-0333/
.. _PasteDeploy: https://docs.pylonsproject.org/projects/pastedeploy/

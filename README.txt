This package contains generic base classes for channel-based servers, the
servers themselves and helper objects, such as tasks and requests.

WSGI support
============

zope.server's HTTP server comes with WSGI_ support.
``zope.server.http.wsgihttpserver.WSGIHTTPServer`` can act as a WSGI
gateway.  There's also an entry point for PasteDeploy_ that lets you
use zope.server's WSGI gateway from a configuration file, e.g.::

  [server:main]
  use = egg:zope.server
  host = 127.0.0.1
  port = 8080

.. _WSGI: http://www.python.org/dev/peps/pep-0333/
.. _PasteDeploy: http://pythonpaste.org/deploy/

Changes
=======

3.4.1 and 3.5.0a2 (2007-06-02)
------------------------------

Made WSGI server really WSGI-compliant by adding variables to the
environment that are required by the spec.

3.5.0a1 (2007-06-02)
--------------------

Added a factory and entry point for PasteDeploy.

3.4.0 (2007-06-02)
------------------

Removed an unused import. Unchanged otherwise.

3.4.0a1 (2007-04-22)
--------------------

Initial release as a separate project, corresponds to zope.server
from Zope 3.4.0a1

zope.server Package Readme
==========================

Overview
--------

Zope 3's Servers.

This package contains generic base classes for channel-based servers, the
servers themselves and helper objects, such as tasks and requests.

Changes
=======

3.4.2 (2008-02-02)
------------------

- Fix of 599 error on conflict error in request
  see: http://mail.zope.org/pipermail/zope-dev/2008-January/030844.html

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

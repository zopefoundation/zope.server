=========
 CHANGES
=========

5.0 (2024-09-05)
================

- Add support for Python 3.10, 3.11.

- Drop support for Python 2.7, 3.5, 3.6.

- Add Python 3.8 and 3.9 support.

- Drop Python 3.4 support.

- Add `python_requires` to `setup.py`.

- Update PasteDeploy link in README.

- Avoid traceback reference cycle in ``_triggerbase.handle_read``.

- Close output buffer when closing a ``DualModeChannel`` to fix a
  ``ResourceWarning``. See `issue 25
  <https://github.com/zopefoundation/zope.server/issues/25>`_.


4.0.2 (2019-07-11)
==================

- Fix pipetrigger.close() to close the right file descriptor.
  (This could've been causing EBADF errors in unrelated places!)

- Add Python 3.7 support.


4.0.1 (2017-10-31)
==================

- Fix Windows compatibility regression introduced in 4.0.0.
  See `issue 9 <https://github.com/zopefoundation/zope.server/issues/9>`_.


4.0.0 (2017-10-30)
==================

- Drop Python 2.6 support.

- Add Python 3.4, 3.5, and 3.6 support.

- Add PyPy support.

- Made the HTTPTask not have ``command`` or ``uri`` values of
  ``"None"`` when the first request line cannot be parsed. Now they
  are empty strings.

- Reimplement ``buffers.OverflowableBuffer`` in terms of the standard
  library's ``tempfile.SpooledTemporaryFile``. This is much simpler.
  See `issue 5 <https://github.com/zopefoundation/zope.server/issues/5>`_.

- Achieve and maintain 100% test coverage.

- Remove all the custom logging implementations in
  ``zope.server.logging`` and change the ``CommonAccessLogger`` and
  ``CommonFTPActivityLogger`` to only work with Python standard
  library loggers. The standard library supports all the logging
  functions this package previously provided. It can be easily configured
  with ZConfig. See `issue 4
  <https://github.com/zopefoundation/zope.server/issues/4>`_.

3.9.0 (2013-03-13)
==================

- Better adherence to WSGI:

  * Call close method if present on iterables returned by
    ``start_response``.

  * Don't include non-string values in the CGI environment
    (``CHANNEL_CREATION_TIME``).

  * Always include ``QUERY_STRING`` to avoid the cgi module falling back
    to ``sys.argv``.

  * Add tests based on `paste.lint` middleware.

- Replaced deprecated ``zope.interface.implements`` usage with equivalent
  ``zope.interface.implementer`` decorator.

- Dropped support for Python 2.4 and 2.5.

- Exceptions that happen in the handler thread main loop are logged so that
  the unexpected death of a handler thread does not happen in silence.


3.8.6 (2012-01-07)
==================

- On startup, HTTPServer prints a clickable URL after the hostname/port.


3.8.5 (2011-09-13)
==================

- fixed bug: requests lasting over 15 minutes were sometimes closed
  prematurely.

3.8.4 (2011-06-07)
==================

- Fix syntax error in tests on Python < 2.6.


3.8.3 (2011-05-18)
==================

- Made ``start_response`` method of WSGI server implementation more compliant
  with spec:

    http://www.python.org/dev/peps/pep-0333/#the-start-response-callable

3.8.2 (2010-12-04)
==================

- Corrected license version in ``zope/server/http/tests/test_wsgiserver.py``.

3.8.1 (2010-08-24)
==================

- When the result of a WSGI application was received, ``task.write()`` was
  only called once to transmit the data. This prohibited the transmission of
  partial results. Now the WSGI server iterates through the result itself
  making multiple ``task.write()`` calls, which will cause partial data to be
  transmitted.

- Created a second test case instance for the post-mortem WSGI server, so it
  is tested as well.

- Using python's ``doctest`` module instead of deprecated
  ``zope.testing.doctest``.

3.8.0 (2010-08-05)
==================

- Implemented correct server proxy behavior. The HTTP server would always add
  a "Server" and "Date" response header to the list of response headers
  regardless whether one had been set already. The HTTP 1.1 spec specifies
  that a proxy server must not modify the "Server" and "Date" header but add a
  "Via" header instead.

3.7.0 (2010-08-01)
==================

- Implemented proxy support. Proxy requests contain a full URIs and the
  request parser used to throw that information away. Using
  ``urlparse.urlsplit()``, all pieces of the URL are recorded.

- The proxy scheme and netloc/hostname are exposed in the WSGI environment as
  ``zserver.proxy.scheme`` and ``zserver.proxy.host``.

- Made tests runnable via buildout again.

3.6.2 (2010-06-11)
==================

- The log message "Exception during task" is no longer logged to the root
  logger but to zope.server.taskthreads.


3.6.1 (2009-10-07)
==================

- Made tests pass with current zope.publisher which restricts redirects to the
  current host by default.


3.6.0 (2009-05-27)
==================

- Moved some imports from test modules to their setUp to prevent
  failures when ZEO tests are run by the same testrunner

- Removed unused dependency on zope.deprecation.

- Remove old zpkg-related DEPENDENCIES.cfg file.


3.5.0 (2008-03-01)
==================

- Improve package meta-data.

- Fix of 599 error on conflict error in request
  see: http://mail.zope.org/pipermail/zope-dev/2008-January/030844.html

- Removed dependency on ZODB.


3.5.0a2 (2007-06-02)
====================

- Made WSGI server really WSGI-compliant by adding variables to the
  environment that are required by the spec.


3.5.0a1 (2007-06-02)
====================

- Added a factory and entry point for PasteDeploy.


3.4.3 (2008-08-18)
==================

- Moved some imports from test modules to their setUp to prevent
  failures when ZEO tests are run by the same testrunner


3.4.2 (2008-02-02)
==================

- Fix of 599 error on conflict error in request
  see: http://mail.zope.org/pipermail/zope-dev/2008-January/030844.html


3.4.1 (2007-06-02)
==================

- Made WSGI server really WSGI-compliant by adding variables to the
  environment that are required by the spec.


3.4.0 (2007-06-02)
==================

- Removed an unused import. Unchanged otherwise.


3.4.0a1 (2007-04-22)
====================

- Initial release as a separate project, corresponds to zope.server
  from Zope 3.4.0a1

- Made WSGI server really WSGI-compliant by adding variables to the
  environment that are required by the spec.

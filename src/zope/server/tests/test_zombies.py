##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Tests for zope.server.serverchannelbase zombie logic
"""
import doctest


class FakeSocket(object):
    data = b''

    def __init__(self, no):
        self.no = no

    def setblocking(self, *args):
        return None

    def close(self, *args):
        return None

    def fileno(self):
        return self.no

    def getpeername(self):
        return ('localhost', self.no)

    def send(self, data):
        raise AssertionError("Never called")

    def recv(self, buflen):
        return b'data'


def zombies_test():
    """Regression test for ServerChannelBase kill_zombies method

    Bug: This method checks for channels that have been "inactive" for a
    configured time. The bug was that last_activity is set at creation time but
    never updated during async channel activity (reads and writes), so any
    channel older than the configured timeout will be closed when a new channel
    is created, regardless of activity.

    >>> import time
    >>> import zope.server.adjustments
    >>> config = zope.server.adjustments.Adjustments()

    >>> from zope.server.serverbase import ServerBase
    >>> class ServerBaseForTest(ServerBase):
    ...     def bind(self, addr):
    ...         ip, port = addr
    ...         print("Listening on %s:%d" % (ip or '*', port))
    >>> sb = ServerBaseForTest('127.0.0.1', 80, start=False, verbose=True)
    Listening on 127.0.0.1:80

    First we confirm the correct behavior, where a channel with no activity
    for the timeout duration gets closed.

    >>> from zope.server.serverchannelbase import ServerChannelBase
    >>> socket = FakeSocket(42)
    >>> channel = ServerChannelBase(sb, socket, ('localhost', 42))

    >>> channel.connected
    True

    >>> channel.last_activity -= int(config.channel_timeout) + 1

    >>> channel.next_channel_cleanup[0] = channel.creation_time - int(
    ...     config.cleanup_interval) - 1

    >>> socket2 = FakeSocket(7)
    >>> channel2 = ServerChannelBase(sb, socket2, ('localhost', 7))

    >>> channel.connected
    False

    Write Activity
    --------------

    Now we make sure that if there is activity the channel doesn't get closed
    incorrectly.

    >>> channel2.connected
    True

    >>> channel2.last_activity -= int(config.channel_timeout) + 1

    >>> channel2.handle_write()

    >>> channel2.next_channel_cleanup[0] = channel2.creation_time - int(
    ...     config.cleanup_interval) - 1

    >>> socket3 = FakeSocket(3)
    >>> channel3 = ServerChannelBase(sb, socket3, ('localhost', 3))

    >>> channel2.connected
    True

    Read Activity
    --------------

    We should test to see that read activity will update a channel as well.

    >>> channel3.connected
    True

    >>> channel3.last_activity -= int(config.channel_timeout) + 1

    >>> import zope.server.http.httprequestparser
    >>> channel3.parser_class = (
    ...    zope.server.http.httprequestparser.HTTPRequestParser)
    >>> channel3.handle_read()

    >>> channel3.next_channel_cleanup[0] = channel3.creation_time - int(
    ...     config.cleanup_interval) - 1

    >>> socket4 = FakeSocket(4)
    >>> channel4 = ServerChannelBase(sb, socket4, ('localhost', 4))

    >>> channel3.connected
    True

    Main loop window
    ----------------

    There is also a corner case we'll do a shallow test for where a
    channel can be closed waiting for the main loop.

    >>> channel4.last_activity -= 1

    >>> last_active = channel4.last_activity

    >>> channel4.set_async()

    >>> channel4.last_activity != last_active
    True

"""


def test_suite():
    return doctest.DocTestSuite()

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

$Id: logger.py,v 1.2 2002/12/25 14:15:26 jim Exp $
"""

from zope.interface import Interface


class IRequestLogger(Interface):
    """This interface describes a requets logger, which logs
    ip addresses and messages.
    """

    def logRequest(ip, message):
        """Logs the ip address and message at the appropriate place."""


"""

$Id: logger.py,v 1.2 2002/12/25 14:15:26 jim Exp $
"""

from zope.interface import Interface


class IMessageLogger(Interface):
    """This interface describes a message logger, which logs
    with the resolution of one message.
    """

    def logMessage(message):
        """Logs the message at the appropriate place."""

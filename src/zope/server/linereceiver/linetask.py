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
"""Line Task
"""
from zope.interface import implementer

from zope.server.interfaces import ITask
from zope.server.task import AbstractTask


@implementer(ITask)
class LineTask(AbstractTask):
    """This is a generic task that can be used with command line
       protocols to handle commands in a separate thread.
    """

    close_on_finish = 0

    def __init__(self, channel, command, m_name):
        AbstractTask.__init__(self, channel)
        self.m_name = m_name
        self.args = command.args

    def _do_service(self):
        """Called to execute the task.
        """
        getattr(self.channel, self.m_name)(self.args)

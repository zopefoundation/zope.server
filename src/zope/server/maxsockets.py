##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""
Find max number of sockets allowed.

.. caution:: These functions are all hard coded to return a constant value
   of 100. Attempting to dynamically compute them by looping and creating
   sockets until failure was very time consuming, at least at one point,
   and at least on macOS. (Anecdotally this has also been observed on other
   platforms too.)

"""
# Medusa max_sockets module.

# several factors here we might want to test:
# 1) max we can create
# 2) max we can bind
# 3) max we can listen on
# 4) max we can connect


def max_select_sockets():
    return 100


max_server_sockets = max_client_sockets = max_select_sockets

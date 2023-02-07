"""
Tests for fixedstramreceiver.py

"""

import unittest

from zope.server import fixedstreamreceiver


class TestFixedStreamReceiver(unittest.TestCase):

    def test_received_with_no_remain(self):
        recv = fixedstreamreceiver.FixedStreamReceiver(-1, None)
        self.assertEqual(0, recv.received(None))

"""
Tests for lineserverchannel.py

"""
import unittest

from zope.server.linereceiver import lineserverchannel
from zope.server.linereceiver.linecommandparser import LineCommandParser


class Channel(lineserverchannel.LineServerChannel):
    # pylint:disable=super-init-not-called,signature-differs
    def __init__(self):
        self.output = []

    def write(self, data):
        self.output.append(data)

    def flush(self, _):
        pass


class TestLineServerChannel(unittest.TestCase):

    def test_unauth(self):
        command = LineCommandParser(None)
        command.cmd = 'not special'
        channel = Channel()
        channel.handle_request(command)

        self.assertEqual(
            channel.output,
            [(Channel.status_messages['LOGIN_REQUIRED']
              + '\r\n').encode("ascii")])

    def test_calls_method(self):
        class Chunnel(Channel):
            authenticated = True
            thing_called = False

            def cmd_thing(self, args):
                self.thing_called = args

        command = LineCommandParser(None)
        command.cmd = 'thing'
        chunnel = Chunnel()
        chunnel.handle_request(command)
        self.assertEqual([], chunnel.output)
        self.assertEqual(chunnel.thing_called, '')

    def test_calls_method_raises_exception(self):
        # Test the exception handling for the method,
        # a broken repr on the channel, and a broken exception
        # object
        class BadException(Exception):
            str_count = 0

            def __str__(self):
                if not self.str_count:
                    self.str_count += 1
                    raise ValueError("Broken exception")
                return Exception.__str__(self)

        class Chunnel(Channel):
            authenticated = True
            thing_called = False
            msgs = ()

            def cmd_thing(self, args):
                self.thing_called = args
                raise BadException("Chunnel")

            def close_when_done(self):
                pass

            def log_info(self, msg, level):
                self.msgs += ((msg, level),)

            def __repr__(self):
                raise Exception("Cant get my repr")

        command = LineCommandParser(None)
        command.cmd = 'thing'
        chunnel = Chunnel()
        chunnel.handle_request(command)
        self.assertIn(b'500 Internal error: ',
                      chunnel.output[0])
        self.assertIn(b'BadException',
                      chunnel.output[0])
        self.assertEqual(chunnel.thing_called, '')
        self.assertEqual(chunnel.msgs[0][1], 'error')

    def test_unknown_command(self):
        class Chunnel(Channel):
            authenticated = True
            # Python 3.4 includes a __getattr__ in asyncore.dispatcher
            # that does `getattr(self.socket, name)`, but self.socket is only
            # set by the constructor in certain circumstances---and we don't
            # call the constructor. This leads to a recursion error unless
            # we make that attribute available here.
            socket = None

        command = LineCommandParser(None)
        command.cmd = 'thing'
        chunnel = Chunnel()
        chunnel.handle_request(command)
        self.assertEqual([b"500 'THING': command not understood.\r\n"],
                         chunnel.output)

    def test_bad_reply_code(self):
        channel = Channel()
        channel.reply('no_such_code')

        self.assertEqual(channel.output,
                         [b'500 Unknown Reply Code: no_such_code.\r\n'])

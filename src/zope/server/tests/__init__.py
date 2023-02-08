import asyncore
import gc
import sys
import time
import traceback
from threading import Event
from threading import Thread

from zope.server.taskthreads import ThreadedTaskDispatcher


class LoopTestMixin:

    thread_name = 'LoopTest'
    task_dispatcher_count = 4

    LOCALHOST = '127.0.0.1'
    SERVER_PORT = 0      # Set these port numbers to 0 to auto-bind, or
    CONNECT_TO_PORT = 0  # use specific numbers to inspect using TCPWatch.

    def setUp(self):
        super().setUp()
        td = self.td = ThreadedTaskDispatcher()
        td.setThreadCount(self.task_dispatcher_count)
        if len(asyncore.socket_map) != 1:  # pragma: no cover
            # Let sockets die off.
            # (tests should be more careful to clear the socket map, and they
            # currently do, but let's keep this backstop just in case, to avoid
            # confusing failures).
            gc.collect()
            asyncore.poll(0.1)
        self.orig_map_size = len(asyncore.socket_map)

        self.server = self._makeServer()

        if self.CONNECT_TO_PORT == 0:
            self.port = self.server.socket.getsockname()[1]
        else:  # pragma: no cover
            self.port = self.CONNECT_TO_PORT
        self.run_loop = 1
        self.counter = 0
        self.thread_started = Event()
        self.thread = Thread(target=self.loop, name=self.thread_name)
        self.thread.setDaemon(True)
        self.thread.start()
        self.thread_started.wait(10.0)
        self.assertTrue(self.thread_started.isSet())

    def tearDown(self):
        self.doCleanups()
        self.run_loop = 0
        self.thread.join()
        self.td.shutdown()
        self.server.close()
        # Make sure all sockets get closed by asyncore normally.
        timeout = time.time() + 5
        while 1:
            # bandage for PyPy: sometimes we were relying on GC to close
            # sockets.
            gc.collect()
            if (len(asyncore.socket_map) <= self.orig_map_size
                    #  Account for the sadly global `the_trigger` defined in
                    # dualchannelmap.
                    or (self.orig_map_size == 0
                        and len(asyncore.socket_map) == 1)):
                # Clean!
                break
            if time.time() >= timeout:  # pragma: no cover
                self.fail('Leaked a socket: %s' % repr(asyncore.socket_map))
            asyncore.poll(0.1)  # pragma: no cover
        super().tearDown()

    def _makeServer(self):
        raise NotImplementedError()

    def loop(self):
        self.thread_started.set()
        import select
        from errno import EBADF
        while self.run_loop:
            self.counter = self.counter + 1
            # Note that it isn't acceptable to fail out of
            # this loop. That will likely make the tests hang.
            try:
                asyncore.poll(0.1)
            except OSError as data:  # pragma: no cover
                print("EXCEPTION POLLING IN LOOP(): %s" % data)
                if data.args[0] == EBADF:
                    for key in asyncore.socket_map:
                        print("")
                        try:
                            select.select([], [], [key], 0.0)
                        except OSError as v:
                            print(f"Bad entry in socket map {key} {v}")
                            print(asyncore.socket_map[key])
                            print(asyncore.socket_map[key].__class__)
                            del asyncore.socket_map[key]
                        else:
                            print("OK entry in socket map %s" % key)
                            print(asyncore.socket_map[key])
                            print(asyncore.socket_map[key].__class__)
                        print("")
            except:  # noqa: E722 do not use bare 'except' pragma: no cover
                print("WEIRD EXCEPTION IN LOOP")
                traceback.print_exception(*(sys.exc_info() + (100,)))

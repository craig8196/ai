#!/usr/bin/env python
# Bzrflag
# Copyright 2008-2011 Brigham Young University
#
# This file is part of Bzrflag.
#
# Bzrflag is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Bzrflag is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Bzrflag.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of Bzrflag, please contact the Copyright
# Licensing Office, Brigham Young University, 3760 HBLL, Provo, UT 84602,
# (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

"""Unit test for BZRFlag module server.py."""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

from cStringIO import StringIO
import asyncore
import os
import unittest

from bzrflag import server, config

LISTEN_SOCK_FILENO = 5
CONN_SOCK_1_FILENO = 11
CONN_SOCK_2_FILENO = 12


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.sock = MockSocket(CONN_SOCK_1_FILENO)

        self.config = {'telnet_console': False}
        self.team = MockTeam()
        self.game = MockGame()
        self.handle_closed_handler = MockHandleClosedHandler()
        self.handler = server.Handler(self.sock, self.team, self.game,
                self.handle_closed_handler, self.config, {})

    def tearDown(self):
        del self.sock
        del self.config
        del self.game
        del self.handle_closed_handler
        del self.handler

    def testAngvel(self):
        self.handshake()
        self.clientWrite('angvel 1 1\n')
        self.serverRead()
        self.assertIn("ok", self.clientRead())

    def testBases(self):
        self.handshake()
        self.clientWrite('bases\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testConstants(self):
        self.handshake()
        #self.clientWrite('constants\n')
        #self.serverRead()
        #self.assertIn("begin", self.clientRead())

    def testFlags(self):
        self.handshake()
        self.clientWrite('flags\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testHelp(self):
        self.handshake()
        self.clientWrite('help\n')
        self.serverRead()
        self.assertIn(":help [command]", self.clientRead())

        self.clientWrite('help help\n')
        self.serverRead()
        self.assertIn("help for a command.", self.clientRead())

    def testMytanks(self):
        self.handshake()
        self.clientWrite('mytanks\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())


    def testObstacles(self):
        self.handshake()
        #self.clientWrite('obstacles\n')
        #self.serverRead()
        #self.assertIn("begin", self.clientRead())

    def testOccgrid(self):
        self.handshake()
        #self.clientWrite('obstacles\n')
        #self.serverRead()
        #self.assertIn("begin", self.clientRead())

    def testOthertanks(self):
        self.handshake()
        self.clientWrite('othertanks\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testQuit(self):
        self.handshake()
        self.clientWrite('quit\n')
        self.serverRead()
        self.assertIn("ok", self.clientRead())

    def testScores(self):
        self.handshake()
        self.clientWrite('scores\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testShoot(self):
        self.handshake()
        self.clientWrite('shoot 1\n')
        self.serverRead()
        self.assertIn("ok", self.clientRead())

    def testShots(self):
        self.handshake()
        self.clientWrite('shots\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testSpeed(self):
        self.handshake()
        self.clientWrite('speed 1 1\n')
        self.serverRead()
        self.assertIn("ok", self.clientRead())

    def testTeams(self):
        self.handshake()
        self.clientWrite('teams\n')
        self.serverRead()
        self.assertIn("begin", self.clientRead())

    def testTimer(self):
        self.handshake()
        self.clientWrite('timer\n')
        self.serverRead()
        self.assertIn("timer 0 0", self.clientRead())

    def handshake(self):
        self.assertEquals(self.clientRead(), 'bzrobots 1\n')
        self.clientWrite('agent 1\n')
        self.serverRead()
        self.assertEquals(self.handler.established, True)

    def serverRead(self):
        self.assertFalse(self.handle_closed_handler.closed)
        asyncore.read(self.handler)

    def clientRead(self):
        return self.sock.remote_read()

    def clientWrite(self, msg):
        self.sock.remote_send(msg)


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.conn_sock_1 = MockSocket(CONN_SOCK_1_FILENO)
        self.conn_sock_2 = MockSocket(CONN_SOCK_2_FILENO)
        socks = [self.conn_sock_1, self.conn_sock_2]
        listen_sock = MockListenSocket(LISTEN_SOCK_FILENO, socks)

        self.config = {'telnet_console': False}
        address = None
        team = MockTeam()
        game = None
        self.asyncore_map = {}
        self.srv = server.Server(address, team, game, self.config,
                listen_sock, self.asyncore_map)

    def tearDown(self):
        del self.conn_sock_1
        del self.conn_sock_2
        del self.config
        del self.asyncore_map

    def testAccept(self):
        self.assertEquals(self.srv.in_use, False)

        # Trigger an accept.
        asyncore.read(self.srv)
        self.assertTrue(CONN_SOCK_1_FILENO in self.asyncore_map)

        self.assertEquals(self.srv.in_use, True)

        # Trigger a second accept, which should fail.
        asyncore.read(self.srv)
        self.assertTrue(self.conn_sock_2.closed)

    def testHandshake(self):
        # Trigger an accept.
        asyncore.read(self.srv)
        handler = self.asyncore_map[CONN_SOCK_1_FILENO]

        # Trigger the handler to write its handshake.
        asyncore.write(handler)
        self.assertEquals(self.conn_sock_1.remote_read(), 'bzrobots 1\n')


class MockGame(object):

    def __init__(self):
        self.timespent = 0
        self.timelimit = 0
        self.num_shots = []
        self.tanks = []
        self.bases = {}
        self.teams = {}
        self.obstacles = []

    def write_msg(self, message):
        pass

    def shots(self):
        for shot in self.num_shots:
            yield shot


class MockTeam(object):

    def __init__(self):
        self.color = 'blue'
        self.tanks = []

    def angvel(self, tankid, value):
        pass

    def speed(self, tankid, value):
        pass

    def shoot(self, tankid):
        return True


class MockListenSocket(object):
    def __init__(self, fileno, socks):
        self._fileno = fileno
        self.socks = socks

    def accept(self):
        sock = self.socks.pop(0)
        #print 'socket!!', sock
        return sock, None

    def fileno(self):
        return self._fileno

    def __getattr__(self, name):
        """Catchall do-nothing"""
        return (lambda *args: None)


class MockSocket(object):
    def __init__(self, fileno):
        self._fileno = fileno
        self.inbuf = ''
        self.outbuf = ''
        self.closed = False

    def fileno(self):
        return self._fileno

    def close(self):
        self.closed = True

    def recv(self, buflen):
        data = self.inbuf[:buflen]
        self.inbuf = self.inbuf[buflen:]
        return data

    def send(self, data):
        self.outbuf += str(data)
        return len(data)

    def remote_recv(self, buflen):
        data = self.outbuf[:buflen]
        self.outbuf = self.outbuf[buflen:]
        return data

    def remote_send(self, data):
        self.inbuf += str(data)
        return len(data)

    def remote_read(self):
        """Read everything in the buffer, for convenience in testing."""
        data = self.outbuf
        self.outbuf = ''
        return data

    def __getattr__(self, name):
        """Catchall do-nothing"""
        return (lambda *args: None)


class MockHandleClosedHandler(object):
    def __init__(self):
        self.closed = False

    def __call__(self):
        self.closed = True

# vim: et sw=4 sts=4

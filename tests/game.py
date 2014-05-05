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

"""Unit test for BZRFlag module game.py."""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import os

import unittest
from bzrflag import game, config


class GameTest(unittest.TestCase):

    def setUp(self):
        path = os.path.dirname(__file__)
        world = "--world="+os.path.join(path, "..", "maps", "test.bzw")
        self.config = config.Config(['--test', world])
        self.game_loop = game.GameLoop(self.config)
        self.game_loop.update_game()
        self.team = "red"

    def tearDown(self):
        del self.game_loop

    def testInitialization(self):
        self.team = self.game_loop.game.teams['green']
        self.assertNotEqual(self.team._obstacles,[])
        self.assertEquals(len(list(self.game_loop.game.tanks())), 40)
        self.assertEquals(len(list(self.game_loop.game.shots())), 0)

# vim: et sw=4 sts=4

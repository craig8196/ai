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

"""Unit test for BZRFlag module config.py."""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import os

import unittest
from bzrflag import config


class ConfigTest(unittest.TestCase):

    def setUp(self):
        path = os.path.dirname(__file__)
        self.world = os.path.join(path, "..", "maps", "test.bzw")
        self.port = "50100"
        self.config_file = config.Config(["--world="+self.world,
                                          "--red-port="+self.port])

    def tearDown(self):
        del self.config_file

    def testArgError(self):
        args = '--world=test_bad.bzw --red-port=50189'.split()
        self.assertRaises(config.ArgumentError, config.Config,args)

    def testOptions(self):
        self.assertEquals(self.config_file['world'], self.world)
        self.assertEquals(self.config_file['red_port'], int(self.port))

# vim: et sw=4 sts=4

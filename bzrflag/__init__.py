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

"""BZRFlag: BZFlag with Robotic Tanks!

"""
__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import logging
import os

import config
import game

LOG_FILENAME = os.path.abspath(os.path.join(
               os.path.split(__file__)[0], '..', 'debug.log'))


def run():
    """Run bzrflag game."""
    config_file = config.Config()
    level = logging.WARNING

    if config_file['debug']:
        level = logging.DEBUG
    fname = config_file.get('debug_out', None)
    logging.basicConfig(level=level, filename=fname)
    g = game.GameLoop(config_file)
    g.loop()

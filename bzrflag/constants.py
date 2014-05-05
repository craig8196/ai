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

"""BZFlag Constants

These constants are originally defined in src/common/global.cxx in the BZFlag
repository.  There are more than a hundred BZFlag constants that are in
global.cxx but are not included in the list of BSFlag constants.

"""

from __future__ import division # Must be at the beginning of the file!

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import math
import logging

logger = logging.getLogger('constants')

# Colors
COLORNAME = ('rogue', 'red', 'green', 'blue', 'purple')

# Tanks
TANKANGVEL = math.pi / 4
TANKLENGTH = 6
TANKRADIUS = 0.72 * TANKLENGTH
TANKSPEED = 25
LINEARACCEL = 0.5
ANGULARACCEL = 0.5
TANKWIDTH = 2.8
TANKALIVE = 'alive'
TANKDEAD = 'dead'
DEADZONE = -999999.0, -999999.0

# Shots
MAXSHOTS = 10
SHOTRADIUS = 0.5
SHOTRANGE = 350
SHOTSPEED = 100
RELOADTIME = SHOTRANGE / SHOTSPEED
SHOTALIVE = 'alive'
SHOTDEAD = 'dead'

# Flags
FLAGRADIUS = 2.5
INITPOINTS = 2000
CAPTUREPOINTS = 4000

# Rules
EXPLODETIME = 5

# Graphics
BASE_PATTERN = '%s_basetop.png'
SHOT_PATTERN = '%s_bolt.png'
FLAG_PATTERN = '%s_flag.png'
TANK_PATTERN = '%s_tank.png'
TILESCALE = 0.1
SHOTSCALE = 2
FLAGSCALE = 3
TANKSCALE = 1.2

FONTSIZE = 16

# A higher loop timeout decreases CPU usage but also decreases the frame rate.
LOOP_TIMEOUT = 0.01

# Server
BACKLOG = 5

# Game
RESPAWNTRIES = 1000




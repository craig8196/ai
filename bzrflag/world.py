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

"""BSFlag World Model

The BSFlag World module implements a parser for reading in bzw files and
creating Python objects for all of the static components of a BZFlag world
(such as bases and obstacles).  It doesn't implement everything because BSFlag
only worries about a subset of BZFlag features anyway.  However, everything
that is supported is implemented correctly.  See the bzw man page for more
information about the file format (but note that their BNF is incomplete).

"""
__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import logging
import math
from pyparsing import nums, Word, Keyword, LineEnd, Each, ZeroOrMore, \
                      Combine, Optional, Dict, SkipTo, Group

import constants

logger = logging.getLogger('world')


def numeric(toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError:
        return float(n)

integer = Word(nums).setParseAction(numeric)

floatnum = Combine(Optional('-') + ('0' | Word('123456789',nums)) +
                   Optional('.' + Word(nums)) +
                   Optional(Word('eE',exact=1) + Word(nums+'+-',nums)))
floatnum.setParseAction(numeric)

end = Keyword('end').suppress()

point2d = floatnum + floatnum
# Note: Since we're just doing 2D, we ignore the z term of 3D points.
point3d = floatnum + floatnum + floatnum.suppress()

# Obstacle
position = Group((Keyword('pos') | Keyword('position')) + point3d)
size = Group(Keyword('size') + point3d)
rotation = Group((Keyword('rot') | Keyword('rotation')) + floatnum)
obstacle_items = [position, Optional(size), Optional(rotation)]


class Box(object):
    """A basic obstacle type."""

    def __init__(self, pos=None, position=None, rot=None, rotation=None,
            size=None):
        self.pos = pos or position
        self.rot = rot or rotation
        if self.rot:
            self.rot *= 2 * math.pi / 360
        self.size = size
        if not self.pos:
            raise ValueError('Position is required')

    @classmethod
    def parser(cls):
        box_contents = Each(obstacle_items)
        box = Dict(Keyword('box').suppress() + box_contents + end)
        box.setParseAction(lambda toks: cls(**dict(toks)))
        return box


class Base(object):
    """A BZFlag Base.  One per team."""

    def __init__(self, color=None, pos=None, position=None, rot=None,
                 rotation=None, size=None):
        self.color = constants.COLORNAME[color]
        self.pos = pos or position
        self.rot = rot or rotation
        if self.rot:
            self.rot *= 2 * math.pi / 360
        self.size = size
        if self.color is None:
            raise ValueError('Color is required')
        if not self.pos:
            raise ValueError('Position is required')

    @classmethod
    def parser(cls):
        color = Group(Keyword('color') + integer)
        base_contents = Each([color] + obstacle_items)
        base = Dict(Keyword('base').suppress() + base_contents + end)
        base.setParseAction(lambda toks: cls(**dict(toks)))
        return base


class World(object):
    """Encompassing class which parses the entire file.  Returns a World
    object that is used by the classes in :mod:`game` to populate the
    game.
    """

    def __init__(self, WIDTH, HEIGHT, items=None):
        self.size = (WIDTH, HEIGHT)
        self.width = WIDTH
        self.height = HEIGHT
        self.boxes = []
        self.bases = []
        if items:
            for item in items:
                if isinstance(item, Box):
                    self.boxes.append(item)
                elif isinstance(item, Base):
                    self.bases.append(item)
                else:
                    raise NotImplementedError('Unhandled world element.')

    @classmethod
    def parser(cls, width, height):
        """Parse a BZW file.

        For now, we're only supporting a subset of BZW's allobjects.
        """
        comment = '#' + SkipTo(LineEnd())
        bzw = ZeroOrMore(Box.parser() | Base.parser()).ignore(comment)
        bzw.setParseAction(lambda toks: cls(width, height, toks))
        return bzw


if __name__ == '__main__':
    f = open('maps/four_ls.bzw')
    parser = World.parser()
    w = parser.parseString(f.read())
    print w

# vim: et sw=4 sts=4

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

"""2D collision testing for BZRFlag game.

point : (x,y)
line : ((ax,ay),(bx,by))
circle : ((x,y),r)
rectangle : (x,y,w,h)
polygon : ((x1,y1),(x2,y2),(x3,y3)...(xn,yn))

"""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import math
import logging

logger = logging.getLogger('collisiontest.py')


def point_in_rect(point, rect):
    """Check if point falls in given rectangle.

    @return: True/False

    >>> rect = (2,3,2,2)
    >>> point_in_rect((3,4), rect)
    True
    >>> point_in_rect((1,2), rect)
    False
    """
    (x, y, w, h) = rect
    poly = ((x,y), (x,y+h), (x+w,y+h), (x+w,y))
    return point_in_poly(point, poly)


def point_in_poly(point, poly):
    """Check if point falls in given polygon.

    @return: True/False

    This method is an implementation of the well known ray casting algorithm.

    >>> poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0, 5))
    >>> point_in_poly((.5,1), poly)
    True
    >>> point_in_poly((5,2), poly)
    False
    >>> point_in_poly((2,2), poly)
    True
    >>> point_in_poly((0,5), poly)
    False
    """
    n = len(poly)
    (x, y) = point
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y) and y <= max(p1y,p2y) and x <= max(p1x,p2x):
            if p1y != p2y:
                xintercept = p1x + (y-p1y)*(p2x-p1x)/(p2y-p1y)
            if p1x == p2x or x <= xintercept:
                inside = not inside
        p1x,p1y = p2x,p2y
    return inside


def line_cross_rect(line, rect):
    """Check if line crosses or falls in given rectangle.

    @return: True/False

    >>> rect = (0,0,4,4)
    >>> line_cross_rect(((1,1), (3,3)), rect)
    True
    >>> line_cross_rect(((3,3), (5,3)), rect)
    True
    >>> line_cross_rect(((5,3), (5,0)), rect)
    False
    >>> line_cross_rect(((5,0), (0,5)), rect)
    True
    """
    (x, y, w, h) = rect
    poly = ((x,y), (x,y+h), (x+w,y+h), (x+w,y))
    return line_cross_poly(line, poly)


def line_cross_poly(line, poly):
    """Check if line crosses or falls in given polygon.

    @return: True/False

    >>> poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0, 5))
    >>> line_cross_poly(((1,1), (2,2)), poly)
    True
    >>> line_cross_poly(((2,2), (5,2)), poly)
    True
    >>> line_cross_poly(((5,2), (0,6)), poly)
    True
    >>> line_cross_poly(((5,2), (5,8)), poly)
    False
    """
    if point_in_poly(line[0], poly) or point_in_poly(line[1], poly):
        return True
    for i,point in enumerate(poly):
        if line_cross_line((point,poly[i-1]), line):
            return True
    return False


def line_cross_line(line_AB, line_CD):
    """Check if given line segments cross.

    @return: True/False

    >>> line = ((0,0), (5,5))
    >>> line_cross_line(line, ((0,1), (1,0)))
    True
    >>> line_cross_line(line, ((6,0), (6,8)))
    False
    >>> line_cross_line(line, ((2,0), (5,3)))
    False
    """

    def clock((p1x,p1y), (p2x,p2y), (p3x,p3y)):
        """True if p1,p2,p3 in clockwise order."""
        return (p3y-p1y)*(p2x-p1x) < (p2y-p1y)*(p3x-p1x)

    (A,B) = line_AB
    (C,D) = line_CD
    return clock(A,C,D) != clock(B,C,D) and clock(A,B,C) != clock(A,B,D)


def line_cross_circle(line, circle):
    """Check if line crosses or falls in given circle.

    @return: True/False

    >>> line = ((1,1), (3,3))
    >>> line_cross_circle(line, ((4,3), 1.1))
    True
    >>> line_cross_circle(line, ((4,3), .9))
    False
    >>> line_cross_circle(line, ((0,0), 7))
    True
    >>> line_cross_circle(line, ((4,4), 1))
    False
    """
    return dist_to_line(circle[0], line) <= circle[1]


def circle_to_rect(circle, rect):
    """Check if circle overlaps or falls in given rectangle.

    @return: True/False

    >>> rect = (2,3,2,2)
    >>> circle_to_rect(((3,4), .1), rect)
    True
    >>> circle_to_rect(((1,2), 1), rect)
    False
    """
    (x, y, w, h) = rect
    poly = ((x,y), (x,y+h), (x+w,y+h), (x+w,y))
    return circle_to_poly(circle, poly)


def circle_to_poly(circle, poly):
    """Check if circle overlaps or falls in given polygon.

    @return: True/False

    >>> poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0, 5))
    >>> circle_to_poly(((3,3), .5), poly)
    True
    >>> circle_to_poly(((5,2), 1.1), poly)
    True
    >>> circle_to_poly(((5,2), .9), poly)
    False
    """
    if point_in_poly(circle[0], poly):
        return True
    for i,point in enumerate(poly):
        if line_cross_circle((point,poly[i-1]), circle):
            return True
    return False


def circle_to_circle(circle1, circle2):
    """Check if circle1 overlaps or falls in circle2.

    @return: True/False

    >>> circle_to_circle(((0,0), 1), ((2,0), 1))
    True
    >>> circle_to_circle(((0,0), 1), ((2.1,0), 1))
    False
    """
    return get_dist(circle1[0],circle2[0]) <= circle1[1] + circle2[1]


def get_dist(point_A, point_B):
    """Calculate distance between two points.

    @return: Pythagorean distance between point_A and point_B.

    >>> get_dist((0,0), (4,3))
    5.0
    """
    (ax,ay) = point_A
    (bx,by) = point_B
    return math.sqrt((bx-ax)**2 + (by-ay)**2)


def dist_to_line(point, line):
    """Calculate distance to nearest point on given line.

    @return: Closest point on line.

    >>> line = ((1,1), (1,3))
    >>> dist_to_line((3,2), line)
    2.0
    >>> dist_to_line((1,4), line)
    1.0
    >>> dist_to_line((2,0), line) == math.sqrt(2)
    True
    """
    # P (px, py): Point of intersection of infinant line (defined by AB) and
    #             its perpendicular passing through  point C.
    # r: Is position of P on infinant line (defined by AB)
    #    where: r = (AC dot AB) / AB_length^2
    #    and:
    #    r = 0  ->  P = A
    #    r = 1  ->  P = B
    #    r < 0  ->  P is on the backward extension of AB
    #    r > 1  ->  P is on the forward extension of AB
    #    0<r<1  ->  P is interior to AB

    (ax,ay) = A = line[0]
    (bx,by) = B = line[1]
    (cx,cy) = C = point
    r = ((cx-ax)*(bx-ax) + (cy-ay)*(by-ay))/get_dist(A,B)**2
    P = (ax + r*(bx-ax), ay + r*(by-ay))
    if r >= 0 and r <= 1:
        return get_dist(C,P)
    else:
        CA_length = get_dist(C,A)
        CB_length = get_dist(C,B)
        if CA_length < CB_length:
            return CA_length
        else:
            return CB_length


if __name__=='__main__':
    import doctest
    doctest.testmod()

# vim: et sw=4 sts=4


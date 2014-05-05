#!/usr/bin/env python
import unittest
import doctest
import math

from bzrflag import collisiontest

class CollisionTest(unittest.TestCase):

    def setUp(self):
        self.c = collisiontest

    def tearDown(self):
        del self.c

    def testPoint(self):
        rect = (0,0,4,4)
        poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0,5))

        self.assertTrue(self.c.point_in_rect((3,3), rect))
        self.assertFalse(self.c.point_in_rect((5,2), rect))

        self.assertTrue(self.c.point_in_poly((.5,1), poly))
        self.assertTrue(self.c.point_in_poly((2,2), poly))
        self.assertFalse(self.c.point_in_poly((5,2), poly))
        self.assertFalse(self.c.point_in_poly((0,5), poly))

    def testLine(self):
        rect = (0,0,4,4)
        line = ((1,1), (3,3))
        poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0,5))

        self.assertTrue(self.c.line_cross_rect(((1,1), (3,3)), rect))
        self.assertFalse(self.c.line_cross_rect(((5,3), (5,0)), rect))

        self.assertTrue(self.c.line_cross_poly(((1,1), (2,2)), poly))
        self.assertTrue(self.c.line_cross_poly(((2,2), (5,2)), poly))
        self.assertTrue(self.c.line_cross_poly(((5,2), (0,6)), poly))
        self.assertFalse(self.c.line_cross_poly(((5,2), (5,8)), poly))

        self.assertTrue(self.c.line_cross_line(line, ((0,3), (3,0))))
        self.assertFalse(self.c.line_cross_line(line, ((6,0), (6,8))))
        self.assertFalse(self.c.line_cross_line(line, ((2,0), (5,3))))

        self.assertTrue(self.c.line_cross_circle(line, ((4,3), 1.1)))
        self.assertTrue(self.c.line_cross_circle(line, ((0,0), 7)))
        self.assertFalse(self.c.line_cross_circle(line, ((4,3), .9)))
        self.assertFalse(self.c.line_cross_circle(line, ((4,4), 1)))

    def testCircle(self):
        rect = (2,3,2,2)
        poly = ((0,0), (4,2), (4,8), (0,7), (2,6), (0,5))

        self.assertTrue(self.c.circle_to_rect(((3,4), .1), rect))
        self.assertFalse(self.c.circle_to_rect(((1,2), 1), rect))

        self.assertTrue(self.c.circle_to_poly(((3,3), .5), poly))
        self.assertTrue(self.c.circle_to_poly(((5,2), 1.1), poly))
        self.assertFalse(self.c.circle_to_poly(((5,2), .9), poly))

        self.assertTrue(self.c.circle_to_circle(((0,0), 1), ((2,0), 1)))
        self.assertFalse(self.c.circle_to_circle(((0,0), 1), ((2.1,0), 1)))

    def testDist(self):
        line = ((1,1), (1,3))

        self.assertEqual(self.c.get_dist((0,0), (4,3)), 5.0)

        self.assertEqual(self.c.dist_to_line((1,4), line), 1.0)
        self.assertEqual(self.c.dist_to_line((3,2), line), 2.0)
        self.assertEqual(self.c.dist_to_line((2,0), line), math.sqrt(2))


# vim: et sw=4 sts=4

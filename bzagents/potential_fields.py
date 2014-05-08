#!/usr/bin/env python
'''This is a demo on how to use Gnuplot for potential fields.  We've
intentionally avoided "giving it all away."
'''
from __future__ import division

import math
import random
import os

from numpy import linspace

def compute_distance(cx, x, cy, y):
    return math.sqrt((cx - x)**2 + (cy - y)**2)

def compute_angle(cx, x, cy, y):
    return math.atan2((cy - y), (cx - x))

def make_circle_attraction_function(cx, cy, cr, cs, a):
    """cx, cy define center, cr is radius, cs is outer radius"""
    def circle_attraction_field(x, y):
        distance = compute_distance(cx, x, cy, y)
        theta = compute_angle(cx, x, cy, y)
        #~ if distance < cr:
            #~ return 0, 0
        #~ elif distance <= (cr + cs):
            #~ return [a * (distance - cr) * math.cos(theta), a * (distance - cr) * math.sin(theta)] 
        #~ else:
            #~ return [a * cs * math.cos(theta), a * cs * math.sin(theta)] 
        if distance < cr:
            return 0, 0
        elif distance > cs:
            return a*math.cos(theta), a*math.sin(theta)
        else:
            max_dist = cs - cr
            dist_to_edge = distance - cr
            dx = (dist_to_edge/max_dist)*math.cos(theta)
            dy = (dist_to_edge/max_dist)*math.sin(theta)
            return a * dx, a * dy
    return circle_attraction_field

def make_circle_repulsion_function(cx, cy, cr, cs, a):
    """cx, cy define center, cr is radius, cs is outer radius"""
    def circle_repulsion_field(x, y):
        xdiff = cx - x
        ydiff = cy - y
        
        distance = math.sqrt(xdiff**2 + ydiff**2)
        theta = math.atan2(ydiff, xdiff)
        
        if distance < cr:
            return a * -math.cos(theta), a * -math.sin(theta)
        elif distance > cs:
            return 0, 0
        else:
            max_dist = cs - cr
            dist_to_edge = cs - distance
            dx = -(dist_to_edge/max_dist)*math.cos(theta)
            dy = -(dist_to_edge/max_dist)*math.sin(theta)
            return a * dx, a * dy
    return circle_repulsion_field

def make_tangential_function(cx, cy, cr, cs, d, a):
    """cx, cy define center, cr is radius, cs is outer radius, d is -1 for counterclockwise and 1 for clockwise"""
    def tangential_function(x, y):
        xdiff = cx - x
        ydiff = cy - y
        distance = math.sqrt(xdiff**2 + ydiff**2)
        theta = math.atan2(ydiff, xdiff)
        theta += d*math.pi/2
        a = 4
        if distance < cr or distance > cs:
            return 0, 0
        else:
            dx = 4 * math.cos(theta)
            dy = 4 * math.sin(theta)
            return a *dx, a * dy
    return tangential_function

def random_field(x, y):
    magnitude = random.uniform(0, 1)
    theta = random.uniform(0, 2*math.pi)
    return magnitude*math.cos(theta), magnitude*math.sin(theta)


########################################################################
# Gnuplot Helper Functions

WORLDSIZE = 800
SAMPLES = 30
VEC_LEN = 0.75 * WORLDSIZE / SAMPLES

def gpi_point(x, y, vec_x, vec_y):
    '''Create the centered gpi data point (4-tuple) for a position and
    vector.  The vectors are expected to be less than 1 in magnitude,
    and larger values will be scaled down.'''
    r = (vec_x ** 2 + vec_y ** 2) ** 0.5
    if r > 1:
        vec_x /= r
        vec_y /= r
    return (x - vec_x * VEC_LEN / 2, y - vec_y * VEC_LEN / 2,
            vec_x * VEC_LEN, vec_y * VEC_LEN)

def gnuplot_header(minimum, maximum):
    '''Return a string that has all of the gnuplot sets and unsets.'''
    s = ''
    s += 'set xrange [%s: %s]\n' % (minimum, maximum)
    s += 'set yrange [%s: %s]\n' % (minimum, maximum)
    # The key is just clutter.  Get rid of it:
    s += 'unset key\n'
    # Make sure the figure is square since the world is square:
    s += 'set size square\n'
    # Add a pretty title (optional):
    #s += "set title 'Potential Fields'\n"
    return s

def draw_line(p1, p2):
    '''Return a string to tell Gnuplot to draw a line from point p1 to
    point p2 in the form of a set command.'''
    x1, y1 = p1
    x2, y2 = p2
    return 'set arrow from %s, %s to %s, %s nohead lt 3\n' % (x1, y1, x2, y2)

def draw_obstacles(obstacles):
    '''Return a string which tells Gnuplot to draw all of the obstacles.'''
    s = 'unset arrow\n'

    for obs in obstacles:
        last_point = obs[0]
        for cur_point in obs[1:]:
            s += draw_line(last_point, cur_point)
            last_point = cur_point
        s += draw_line(last_point, obs[0])
    return s

def plot_field(function):
    '''Return a Gnuplot command to plot a field.'''
    s = "plot '-' with vectors head\n"

    separation = WORLDSIZE / SAMPLES
    end = WORLDSIZE / 2 - separation / 2
    start = -end

    points = ((x, y) for x in linspace(start, end, SAMPLES)
                for y in linspace(start, end, SAMPLES))

    for x, y in points:
        f_x, f_y = function(x, y)
        plotvalues = gpi_point(x, y, f_x, f_y)
        if plotvalues is not None:
            x1, y1, x2, y2 = plotvalues
            s += '%s %s %s %s\n' % (x1, y1, x2, y2)
    s += 'e\n'
    return s

# vim: et sw=4 sts=4

#!/usr/bin/env python
'''This is a demo on how to use Gnuplot for potential fields.  We've
intentionally avoided "giving it all away."
'''
from __future__ import division


import math
import random
import os


from numpy import linspace

# Vector math
def length_squared(v1, v2):
    """Return |v1-v2|^2."""
    return (v1[0] - v2[0])**2 + (v1[1] - v2[1])**2

def calc_distance(v1, v2):
    """Return distance between 2 tuples of length 2."""
    return math.sqrt(length_squared(v1, v2))

def dot_product(v1, v2):
    """Return dot product of 2 tuples length 2."""
    return v1[0]*v2[0] + v1[1]*v2[1]

def calc_vector(x1, y1, x2, y2, max_distance, angle):
    xdiff = x2 - x1
    ydiff = y2 - y1
    d = math.sqrt(xdiff**2 + ydiff**2)
    if d > max_distance:
        return 0, 0
    else:
        theta = math.atan2(ydiff, xdiff)
        theta += angle*math.pi/180
        dx = ((max_distance - d)/max_distance)*math.cos(theta)
        dy = ((max_distance - d)/max_distance)*math.sin(theta)
        return dx, dy

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

def make_line_function(x1, y1, x2, y2, max_distance=10, angle=180):
    """x1, y1 and x2, y2 are the start and end points of the line.
    Return a function.
    """
    def line_field(x, y):
        len_sqrd = length_squared((x1, y1), (x2, y2))
        if len_sqrd == 0.0:
            return calc_vector(x, y, x1, y1, max_distance, angle)
        t = dot_product((x - x1, y - x1), (x2 - x1, y2 - y1)) / len_sqrd
        if t < 0.0:
            return calc_vector(x, y, x1, y1, max_distance, angle)
        elif t > 1.0:
            return calc_vector(x, y, x2, y2, max_distance, angle)
        else:
            newx = x1 + t*(x2 - x1)
            newy = y1 + t*(y2 - y1)
            return calc_vector(x, y, newx, newy, max_distance, angle)
    return line_field

def random_field(x, y):
    magnitude = random.uniform(0, 1)
    theta = random.uniform(0, 2*math.pi)
    return magnitude*math.cos(theta), magnitude*math.sin(theta)

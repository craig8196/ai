#!/usr/bin/env python
'''This is a demo on how to use Gnuplot for potential fields.  We've
intentionally avoided "giving it all away."
'''

from __future__ import division
from itertools import cycle
import math
import random
import os

try:
    from numpy import linspace
except ImportError:
    # This is stolen from numpy.  If numpy is installed, you don't
    # need this:
    def linspace(start, stop, num=50, endpoint=True, retstep=False):
        """Return evenly spaced numbers.

        Return num evenly spaced samples from start to stop.  If
        endpoint is True, the last sample is stop. If retstep is
        True then return the step value used.
        """
        num = int(num)
        if num <= 0:
            return []
        if endpoint:
            if num == 1:
                return [float(start)]
            step = (stop-start)/float((num-1))
            y = [x * step + start for x in xrange(0, num - 1)]
            y.append(stop)
        else:
            step = (stop-start)/float(num)
            y = [x * step + start for x in xrange(0, num)]
        if retstep:
            return y, step
        else:
            return y


########################################################################
# Constants

# Output file:
FILENAME = 'fields.gpi'
# Size of the world (one of the "constants" in bzflag):
WORLDSIZE = 800
# How many samples to take along each dimension:
SAMPLES = 50
# Change spacing by changing the relative length of the vectors.  It looks
# like scaling by 0.75 is pretty good, but this is adjustable:
VEC_LEN = 0.75 * WORLDSIZE / SAMPLES
# Animation parameters:
ANIMATION_MIN = 0
ANIMATION_MAX = 500
ANIMATION_FRAMES = 100


########################################################################
# Field and Obstacle Definitions

def generate_field_function(scale):
    def function(x, y):
        '''User-defined field function.'''
        sqnorm = (x**2 + y**2)
        if sqnorm == 0.0:
            return 0, 0
        else:
            return x*scale/sqnorm, y*scale/sqnorm
    return function

OBSTACLES = [((0, 0), (-150, 0), (-150, -50), (0, -50)),
                ((200, 100), (200, 330), (300, 330), (300, 100))]


# Vector math
def length_squared(v1, v2):
    return (v1[0] - v2[0])**2 + (v1[1] - v2[1])**2

def distance(v1, v2):
    return math.sqrt(length_squared(v1, v2))

def dot_product(v1, v2):
    return v1[0]*v2[0] + v1[1]*v2[1]

def make_circle_attraction_function(cx, cy, cr, cs):
    """cx, cy define center, cr is radius, cs is outer radius.
    Return a function.
    """
    def circle_attraction_field(x, y):
        xdiff = cx - x
        ydiff = cy - y
        
        distance = math.sqrt(xdiff**2 + ydiff**2)
        theta = math.atan2(ydiff, xdiff)
        
        if distance < cr:
            return 0, 0
        elif distance > cs:
            return math.cos(theta), math.sin(theta)
        else:
            max_dist = cs - cr
            dist_to_edge = distance - cr
            dx = (dist_to_edge/max_dist)*math.cos(theta)
            dy = (dist_to_edge/max_dist)*math.sin(theta)
            return dx, dy
    return circle_attraction_field

def make_circle_repulsion_function(cx, cy, cr, cs):
    """cx, cy define center, cr is radius, cs is outer radius.
    Return a function.
    """
    def circle_repulsion_field(x, y):
        xdiff = cx - x
        ydiff = cy - y
        
        distance = math.sqrt(xdiff**2 + ydiff**2)
        theta = math.atan2(ydiff, xdiff)
        
        if distance < cr:
            return -math.cos(theta), -math.sin(theta)
        elif distance > cs:
            return 0, 0
        else:
            max_dist = cs - cr
            dist_to_edge = cs - distance
            dx = -(dist_to_edge/max_dist)*math.cos(theta)
            dy = -(dist_to_edge/max_dist)*math.sin(theta)
            return dx, dy
    return circle_repulsion_field

def make_tangential_function(cx, cy, cr, cs, d):
    """cx, cy define center, cr is radius, cs is outer radius, 
    d is -1 for counterclockwise and 1 for clockwise.
    Return a function.
    """
    def tangential_function(x, y):
        xdiff = cx - x
        ydiff = cy - y
        distance = math.sqrt(xdiff**2 + ydiff**2)
        theta = math.atan2(ydiff, xdiff)
        theta += d*math.pi/2
        if distance < cr or distance > cs:
            return 0, 0
        else:
            dx = math.cos(theta)
            dy = math.sin(theta)
            return dx, dy
    return tangential_function

def random_field(x, y):
    magnitude = random.uniform(0, 1)
    theta = random.uniform(0, 2*math.pi)
    return magnitude*math.cos(theta), magnitude*math.sin(theta)

def make_line_function(x1, y1, x2, y2, parallel=1, distance=10):
    """x1, y1 and x2, y2 are the start and end points of the line.
    parallel determines how parallel to the line the tank is.
    distance is the distance from the line the field is in effect.
    Return a function.
    """
    def line_field(x, y):
        len_sqrd = length_squared((x1, y1), (x2, y2))
        # TODO finish this
        if len_sqrd == 0.0:
            return 
        return 0, 0
    return line_field

def combined_field1(x, y):
    r1 = make_circle_attraction_function(0, 0, 50, 300)(x, y)
    r2 = make_circle_repulsion_function(0, 0, 50, 300)(x, y)
    return r1[0] + r2[0], r1[1] + r2[1]

def combined_field2(x, y):
    r1 = make_circle_attraction_function(100, 100, 50, 300)(x, y)
    r2 = make_circle_repulsion_function(-50, -50, 50, 150)(x, y)
    return r1[0] + r2[0], r1[1] + r2[1]





########################################################################
# Helper Functions

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


########################################################################
# Plot the potential fields to a file

functions_to_plot = {
    'example_field.gpi': generate_field_function(150),
    'circle_attractive_field.gpi': make_circle_attraction_function(0, 0, 50, 300),
    'circle_repulsion_field.gpi': make_circle_repulsion_function(0, 0, 50, 300),
    'combined_field1.gpi': combined_field1,
    'combined_field2.gpi': combined_field2,
    'random_field.gpi': random_field,
    'counterclockwise_tangential_function.gpi': make_tangential_function(0, 0, 50, 300, -1),
    'clockwise_tangential_function.gpi': make_tangential_function(0, 0, 50, 300, 1),
}

def create_gpi_files(functions, directory):
    """Create gpi files for each field function in functions.
    f is dict of file name to function where function will be plotted.
    """
    if not os.path.exists(directory):
        os.mkdirs(directory)
    
    for file_name, function in functions.iteritems():
        with open(os.path.join(directory, file_name), 'w') as outfile:
            print >>outfile, gnuplot_header(-WORLDSIZE / 2, WORLDSIZE / 2)
            print >>outfile, plot_field(function)

# plot all listed functions
create_gpi_files(functions_to_plot, 'gnuplot_fields')

########################################################################
# Animate a changing field, if the Python Gnuplot library is present

try:
    from Gnuplot import GnuplotProcess
except ImportError:
    print "Sorry.  You don't have the Gnuplot module installed."
    import sys
    sys.exit(-1)

forward_list = list(linspace(ANIMATION_MIN, ANIMATION_MAX, ANIMATION_FRAMES/2))
backward_list = list(linspace(ANIMATION_MAX, ANIMATION_MIN, ANIMATION_FRAMES/2))
anim_points = forward_list + backward_list
 
gp = GnuplotProcess(persist=False)
gp.write(gnuplot_header(-WORLDSIZE / 2, WORLDSIZE / 2))
gp.write(draw_obstacles(OBSTACLES))
 
while True:
    gp.write(plot_field(combined_field1()))
for scale in cycle(anim_points):
    field_function = generate_field_function(scale)
    gp.write(plot_field(field_function))

# vim: et sw=4 sts=4

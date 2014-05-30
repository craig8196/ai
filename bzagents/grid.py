#!/usr/bin/env python
from __future__ import division
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy
from numpy import zeros
from threading import Thread, Lock, Event
import time
from utilities import ThreadSafeQueue
import random


class ObstacleVisualization(Thread):
    def __init__(self, width, height):
        super(ObstacleVisualization, self).__init__()
        self.grid = None
        self.width = width
        self.height = height
        self.lock = Lock()
        self.updated = Event()
        self.updated.clear()
        self.ext_grid = None # external grid
        
    def set_external_grid(self, ext_grid):
        self.ext_grid = ext_grid
    
    def run(self):
        self.init_window(self.width, self.height)
    
    def draw_grid(self):
        # This assumes you are using a numpy array for your grid
        width, height = self.grid.shape
        glRasterPos2f(-1, -1)
        glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, self.grid)
        glFlush()
        glutSwapBuffers()
    
    def on_idle(self):
        self.updated.wait(1.0)
        self.updated.clear()
        if self.ext_grid:
            self.update_grid(self.ext_grid.obstacle_grid.copy().T) # Use discrete values
            #~ self.update_grid(self.ext_grid.grid.copy().T) # Use range of probabilities
            glutPostRedisplay()
    
    def update_grid(self, new_grid):
        self.lock.acquire()
        self.grid = new_grid
        self.lock.release()
    
    def update_grid_values(self, num):
        self.lock.acquire()
        self.grid[:] = num
        self.lock.release()

    def init_window(self, width, height):
        self.grid = zeros((width, height))
        self.lock.acquire()
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
        glutInitWindowSize(width, height)
        glutInitWindowPosition(0, 0)
        self.window = glutCreateWindow("Grid Filter")
        glutDisplayFunc(self.draw_grid)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        self.lock.release()
        glutIdleFunc(self.on_idle)
        glutMainLoop()

class Grid(Thread):
    INITIAL_OBSTACLE_PROBABILITY = 0.95
    DEFAULT_TRUE_POSITIVE = 0.25
    DEFAULT_TRUE_NEGATIVE = 0.25
    OBSTACLE = 1
    NOT_OBSTACLE = 0
    UNKNOWN = 0.5
    
    def __init__(self, width, height):
        super(Grid, self).__init__()
        self.grid = numpy.empty((width, height))
        self.grid[:] = Grid.INITIAL_OBSTACLE_PROBABILITY
        self.obstacle_grid = numpy.empty((width, height))
        self.obstacle_grid[:] = Grid.UNKNOWN
        self.accessible_unknowns = [(0, 0)]
        self.set_true_positive(Grid.DEFAULT_TRUE_POSITIVE)
        self.set_true_negative(Grid.DEFAULT_TRUE_NEGATIVE)
        self.update_thresholds()
        self.events = []
        
        self.vis = ObstacleVisualization(width, height)
        self.add_update_event(self.vis.updated)
        self.vis.set_external_grid(self)
        self.vis.start()
        
        self.unknowns_update_frequency = 20.0 # number of seconds before we refresh
        self.lock = Lock()
        self.grids_to_update = ThreadSafeQueue()
        
        self.unknowns_updater = Thread(target=self.run_updater)
        self.unknowns_updater.start()
        self.start()
    
    def run_updater(self):
        time.sleep(self.unknowns_update_frequency)
        self.update_unknowns()
    
    def run(self):
        x, y, mini_grid = self.grids_to_update.remove()
        self.update(x, y, mini_grid)
    
    def is_unknown(self, x, y):
        x = int(x)
        y = int(y)
        xlen, ylen = self.obstacle_grid.shape
        if x < 0 or y < 0 or x >= xlen or y >= ylen:
            return False
        if self.obstacle_grid[x, y] == Grid.UNKNOWN:
            return True
        return False
    
    def update_unknowns(self):
        self.lock.acquire()
        if self.accessible_unknowns != None:
            (i_len, j_len) = self.grid.shape
            self.accessible_unknowns = []
            for i in xrange(1, i_len-1):
                for j in xrange(1, j_len-1):
                    if self.obstacle_grid[i][j] == Grid.UNKNOWN:
                        if self.obstacle_grid[i-1][j] == Grid.NOT_OBSTACLE or \
                           self.obstacle_grid[i+1][j] == Grid.NOT_OBSTACLE or \
                           self.obstacle_grid[i][j-1] == Grid.NOT_OBSTACLE or \
                           self.obstacle_grid[i][j+1] == Grid.NOT_OBSTACLE:
                            self.accessible_unknowns.append((i,j))
            print "Remaining points to get: " + str(len(self.accessible_unknowns))
            if len(self.accessible_unknowns) == 0:
                self.accessible_unknowns = None
        self.lock.release()
    
    def are_there_accessible_unknowns(self):
        if self.accessible_unknowns == None:
            return False
        return True
    
    def get_random_unknown_point(self):
        l = self.accessible_unknowns
        if l == None or len(l) == 0:
            return (-1, -1)
        else:
            return l[random.randint(0, len(l) - 1)]
    
    def get_unknown_pointset(self, x, y, size=100):
        """x and y are integers"""
        xlen, ylen = self.obstacle_grid.shape
        xmax = size
        ymax = size
        x = x - int(xmax/2)
        y = y - int(ymax/2)
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x >= xlen:
            x = xlen - 1
        if y >= ylen:
            y = ylen - 1
        if x + xmax > xlen:
            xmax -= x + xmax - xlen
        if y + ymax > ylen:
            ymax -= y + ymax - ylen
        
        point_set = []
        # find unknowns
        for i in xrange(0, xmax):
            for j in xrange(0, ymax):
                if self.obstacle_grid[x + i, y + j] == Grid.UNKNOWN:
                    point_set.append((i, j))
        
        return point_set
    
    def update_thresholds(self):
        self.obstacle_threshold = self.cond_prob_obstacle_obstacle + (1 - self.cond_prob_obstacle_obstacle)/2# any probability above this is considered an obstacle
        self.not_obstacle_threshold = self.cond_prob_obstacle_not_obstacle - self.cond_prob_obstacle_not_obstacle/2 # any probability below this is considered to not be an obstacle
        if self.obstacle_threshold < self.not_obstacle_threshold:
            temp = self.not_obstacle_threshold
            self.not_obstacle_threshold = self.obstacle_threshold
            self.obstacle_threshold = temp
    
    def add_update_event(self, event):
        """Add an event that gets notified upon updating."""
        self.events.append(event)
    
    def notify_update_event(self):
        for e in self.events:
            e.set()
    
    def get_shape(self):
        return self.grid.shape
    
    def set_true_positive(self, prob):
        self.prob_true_positive = prob
        # P(o_i,j=obstacle|s_i,j=obstacle)
        self.cond_prob_obstacle_obstacle = self.prob_true_positive
        # P(o_i,j=not_obstacle|s_i,j=obstacle)
        self.cond_prob_not_obstacle_obstacle = 1 - self.cond_prob_obstacle_obstacle
    
    def set_true_negative(self, prob):
        self.prob_true_negative = prob
        # P(o_i,j=not_obstacle|s_i,j=not_obstacle)
        self.cond_prob_not_obstacle_not_obstacle = self.prob_true_negative
        # P(o_i,j=obstacle|s_i,j=not_obstacle)
        self.cond_prob_obstacle_not_obstacle = 1 - self.cond_prob_not_obstacle_not_obstacle
    
    def update_cell(self, i, j, observation):
        # WARNING: helper function to update() do not acquire locks
        # update new probability
        self.grid[i, j] = self.calculate_conditional_probability(self.grid[i, j], observation)
        # update obstacle_grid
        if self.grid[i, j] < self.not_obstacle_threshold:
            self.obstacle_grid[i, j] = self.NOT_OBSTACLE
        elif self.grid[i, j] > self.obstacle_threshold:
            self.obstacle_grid[i, j] = self.OBSTACLE
        else:
            self.obstacle_grid[i, j] = 0.5

    #returns P(s_i,j = occupied | o_i,j) the main conditional probability that we want
    def calculate_conditional_probability(self, prob_state_is_obstacle, observation):
        """Return the new probability that a cell contains an obstacle."""
        # P(s_i,j=obstacle | o_i,j=obstacle)
        if observation == Grid.OBSTACLE:
            cp_obs_obs_1 = self.cond_prob_obstacle_obstacle*prob_state_is_obstacle
            cp_obs_obs_2 = self.cond_prob_obstacle_not_obstacle*(1 - prob_state_is_obstacle)
            return cp_obs_obs_1/(cp_obs_obs_1 + cp_obs_obs_2)
        elif observation == Grid.NOT_OBSTACLE:
            cp_obs_not_obs_1 = self.cond_prob_not_obstacle_obstacle*(prob_state_is_obstacle)
            cp_obs_not_obs_2 = self.cond_prob_not_obstacle_not_obstacle*(1-prob_state_is_obstacle)
            return cp_obs_not_obs_1/(cp_obs_not_obs_1 + cp_obs_not_obs_2)
        else:
            return prob_state_is_obstacle # no observation, return previous state
    
    def get_value(self, x, y):
        return self.grid[x, y]
    
    def update_unexplored_percentage(self):
        """Set the ambiguous percentage, which is the amount of the map
        that we don't have explored.
        """
        if time.time() - self.last_unexplored_update > self.unexplored_update:
            xlen, ylen = self.grid.shape
            count = 0
            for i in xrange(0, xlen):
                for j in xrange(0, ylen):
                    if self.obstacle_grid[i, j] == self.UNKNOWN:
                        count += 1
            self.unexplored_percentage = count/(xlen*ylen)
            print "Unexplored percentage: " + str(self.unexplored_percentage)
    
    def add_grid_update(self, x, y, mini_grid):
        self.grids_to_update.add((x, y, mini_grid))
    
    def update(self, corner_x, corner_y, mini_grid):
        """mini_grid is a numpy matrix of ones and zeros
        The corner is the starting corner in the map when rotated correctly.
        """
        self.lock.acquire()
        (i_len, j_len) = mini_grid.shape
        
        for i in xrange(0, i_len):
            for j in xrange(0, j_len):
                self.update_cell(i + corner_x, j + corner_y, mini_grid[i, j])
        
        self.notify_update_event()
        self.lock.release()

if __name__ == "__main__":
    ov = ObstacleVisualization(800, 800)
    ov.start()
    num = 0
    inc = 0.05
    while ov.is_alive():
        num += inc
        ov.update_grid_values(num)
        time.sleep(1)
        if num >= 1:
            inc *= -1
        ov.updated.set()
    ov.join()

# vim: et sw=4 sts=4

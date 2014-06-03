from __future__ import division
import sys
import math
import time
import random
import numpy
from bzrc import BZRC, Command
from potential_fields import *
from env import EnvironmentState
from base_tank import Tank
from graph import KalmanHeatMapGraph

class KalmanFilter(object):
    def __init__(self, std_dev_x=5, std_dev_y=5):
        self.std_dev_x = std_dev_x
        self.std_dev_y = std_dev_y
        # covariance matrix of x and y
        self.sigma_z = numpy.matrix([[std_dev_x**2, 0],[0, std_dev_y**2]])
        # observation matrix, selects for the position
        self.H = numpy.matrix([[1,0,0,0,0,0],[0,0,0,1,0,0]])
        self.HT = self.H.T
        # covariance matrix for position, velocity, and acceleration for x and y
        self.sigma_x = numpy.zeros((6, 6))
        self.sigma_x[0, 0] = 0.1
        self.sigma_x[1, 1] = 0.1
        self.sigma_x[2, 2] = 50
        self.sigma_x[3, 3] = 0.1
        self.sigma_x[4, 4] = 0.1
        self.sigma_x[5, 5] = 50
        # initialize Newtonian physics matrix
        self.set_F()
        # covariance matrix for position, velocity, and acceleration for x and y
        self.sigma_t = numpy.zeros((6, 6))
        self.sigma_t[0, 0] = 100
        self.sigma_t[1, 1] = 0.1
        self.sigma_t[2, 2] = 0.1
        self.sigma_t[3, 3] = 100
        self.sigma_t[4, 4] = 0.1
        self.sigma_t[5, 5] = 0.1
        # the mean position vector
        self.mu_t = numpy.zeros((6, 1))
        # the identity matrix
        self.identity = numpy.zeros((6, 6))
        for i in range(self.identity.shape[0]):
            self.identity[i][i] = 1
        # keep track of total time change
        self.time_from_start = 0
        
    def set_F(self, delta_t=0.2, friction=0):
        self.F = numpy.zeros((6, 6))
        self.delta_t = delta_t
        self.friction = friction
        (x_len, y_len) = self.F.shape
        
        # set diagonal to 1
        for i in range(x_len):
            self.F[i, i] = 1
        F = self.F
        F[0, 1] = delta_t
        F[1, 2] = delta_t
        F[3, 4] = delta_t
        F[4, 5] = delta_t
        F[0, 2] = (delta_t**2)/2
        F[3, 5] = (delta_t**2)/2
        F[2, 1] = friction
        F[5, 4] = friction
        self.FT = self.F.T
    
    def add_time(self, time_amount):
        self.time_from_start += time_amount
    
    def next_observed_z(self, x, y):
        """Return the predicted location of the tank, mu_t+1."""
        Z = numpy.zeros((2, 1))
        Z[0, 0] = x
        Z[1, 0] = y
        # make common computation since the expression (F(sigma-t)FT + sigma-x) occurs three times
        common = self.F.dot(self.sigma_t).dot(self.FT) + self.sigma_x
        # make K + 1 computation
        K1 = common.dot(self.HT).dot((self.H.dot(common).dot(self.HT) + self.sigma_z).I)
        # make mu t + 1 computation, update previous variable
        self.mu_t = self.F.dot(self.mu_t) + K1.dot(Z - self.H.dot(self.F).dot(self.mu_t))
        # make sigma t + 1 computation, update previous variable
        self.sigma_t = (self.identity - K1.dot(self.H)).dot(common)
        self.add_time(self.delta_t)
        return self.mu_t[0, 0], self.mu_t[3, 0]

'''Note: when a MatrixManager object calls the method set_index_list(), it is taking as a parameter 
index_list which implicitly stores row-column index pairs in the following format: [row_1, column_1, row_2, column_2, ....]
And for each of the cells thus specified in the index_list that is passed to the method, the value is set as the
value that is passed in as the first parameter for the method

Also, if you want to access the matrix itself from a MatrixManager object, then do: 
m.values
'''
class KalmanTank(Tank):
    def __init__(self, bzrc, index, debug, color):
        super(KalmanTank, self).__init__(bzrc, index, debug, color)
        self.change_in_t = 0.2
        self.friction = 0
        self.position_variance = 0.1
        self.velocity_variance = 0.1
        self.acceleration_variance = 100
        self.position_noise = 5
        self.last_time_updated = -1
        self.constants = bzrc.get_environment_constants()
        self.filter = KalmanFilter(self.position_noise, self.position_noise)
        self.kalmangraph = KalmanHeatMapGraph()
        self.kalmangraph.start()
    
    def behave(self, time_diff, env_state):
        commands = []
        if self.last_time_updated == -1:
            self.last_time_updated = time_diff
        if time_diff - self.last_time_updated < self.change_in_t:
            return commands
        
        self.last_time_updated = time_diff
        mytank = env_state.get_mytank(self.index)
        othertank = self.othertanks[0]
        self.filter.set_F(time_diff - self.filter.time_from_start)
        estimated_pos = self.filter.next_observed_z(othertank.x, othertank.y)
        self.kalmangraph.add(estimated_pos, self.filter.sigma_z)
        
        commands.append(self.aim(mytank, estimated_pos))
        return commands
    
    def aim(self, mytank, target_pos):
        print target_pos
        self.filter.set_F(0.2)
        future_mu = self.filter.F.dot(self.filter.mu_t)
        future_pos = (future_mu[0,0], future_mu[3, 0])
        curr_angle = math.atan2(target_pos[1] - mytank.y, target_pos[0] - mytank.x)
        future_angle = math.atan2(future_pos[1] - mytank.y, future_pos[0] - mytank.x)
        curr_dist = math.sqrt((target_pos[0] - mytank.x)**2 + (target_pos[1] - mytank.y)**2)
        future_dist = math.sqrt((future_pos[0] - mytank.x)**2 + (future_pos[1] - mytank.y)**2)
        
        self.filter.set_F(future_dist/350)
        fire_mu = self.filter.F.dot(self.filter.mu_t)
        fire_pos = (fire_mu[0,0], fire_mu[3, 0])
        fire_dist = math.sqrt((fire_pos[0] - mytank.x)**2 + (fire_pos[1] - mytank.y)**2)
        fire_angle = math.atan2(fire_pos[1] - mytank.y, fire_pos[0] - mytank.x)
        fire_delta = abs(math.asin(8/fire_dist))
        if abs(fire_angle - mytank.angle) < fire_angle and fire_dist <= 350:
            fire = True
        else:
            fire = False
        
        angvel = 2*self.normalize_angle(fire_angle - mytank.angle)
        print mytank.angle, fire_angle, angvel
        return Command(mytank.index, 0, angvel, fire)
    
    def get_angvel(self, myang, targetang):
        ang = targetang-myang
        ang = self.normalize_angle(ang)
        print "Ang:", ang
        if ang < 0:
            angvel = -1
        else:
            angvel = 1
        
        if abs(ang) < 1:
            angvel *= ang/1.5
        
        print angvel
        
        return angvel

def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))
    agent = KalmanTank(bzrc, 0, True, "green")
    # agent = KalmanTank(None, 0, True, "green")
    agent.play()


if __name__ == '__main__':
    main()




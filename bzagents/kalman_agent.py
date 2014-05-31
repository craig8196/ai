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

class MatrixManager(object):
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.values = numpy.empty((self.height, self.width))

	def set_all_values(self, value):
		self.values[:] = value

	def transpose_matrix(self):
		return self.values.T

	def set_index_list(self, value, index_list):
		set_row_value = True
		for i in index_list:
			if set_row_value:
				row_value = i
				set_row_value = False
			else:
				self.values[row_value][i] = value
				set_row_value = True

	def print_matrix(self):
		for i in range(self.height):
			for j in range(self.width):
				print(str(self.values[i][j])),
			print "\n"

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

        #these are the six matrices which the lab specs say can be initialized or precomputed just once:

        #Note that these four matrices are constants, so can be initialized once: F, sigma-x, H, sigma-z
		#Note also that since H and F are constant, HT and FT are also constant, and can be precomputed just once.
	
        self.init_f_matrix()
        self.init_transpose_f_matrix()
        self.init_h_matrix()
        self.init_transpose_h_matrix()
        self.init_sigma_x_matrix()
        self.init_sigma_z_matrix()

        #these are the two matrices which are updated each time slice
        self.init_mu_t_matrix()
        self.init_sigma_t_matrix()

    def init_f_matrix(self):
    	width = 6
    	height = 6
    	self.f_matrix = MatrixManager(width, height)
    	self.f_matrix.set_all_values(0)
    	for i in range(6):
    		self.f_matrix.values[i][i] = 1
    	index_list = [0, 1, 1, 2, 3, 4, 4, 5]
    	self.f_matrix.set_index_list(self.change_in_t, index_list)
    	index_list = [0, 2, 3, 5]
    	self.f_matrix.set_index_list((self.change_in_t**2) / 2, index_list)
        index_list = [2, 1, 5, 4]
        self.f_matrix.set_index_list(self.friction, index_list)
        # self.f_matrix.print_matrix()

    def init_transpose_f_matrix(self):
    	self.transpose_f_matrix = MatrixManager(self.f_matrix.height, self.f_matrix.width)
    	self.transpose_f_matrix.values = self.f_matrix.transpose_matrix()
    	# self.transpose_f_matrix.print_matrix()

    def init_h_matrix(self):
    	width = 6
    	height = 2
    	self.h_matrix = MatrixManager(width, height)
    	self.h_matrix.set_all_values(0)
    	index_list = [0, 0, 1, 3]
    	self.h_matrix.set_index_list(1, index_list)
    	# self.h_matrix.print_matrix()

    def init_transpose_h_matrix(self):
    	self.transpose_h_matrix = MatrixManager(self.h_matrix.height, self.h_matrix.width)
    	self.transpose_h_matrix.values = self.h_matrix.transpose_matrix()
    	# self.transpose_h_matrix.print_matrix()

    def init_sigma_x_matrix(self):
    	width = 6
    	height = 6
    	self.sigma_x_matrix = MatrixManager(width, height)
    	self.sigma_x_matrix.set_all_values(0)
    	index_list = [0, 0, 3, 3]
    	self.sigma_x_matrix.set_index_list(self.position_variance, index_list)
    	index_list = [1, 1, 4, 4]
    	self.sigma_x_matrix.set_index_list(self.velocity_variance, index_list)
    	index_list = [2, 2, 5, 5]
    	self.sigma_x_matrix.set_index_list(self.acceleration_variance, index_list)
    	# self.sigma_x_matrix.print_matrix()

    def init_sigma_z_matrix(self):
    	width = 2
    	height = 2
    	self.sigma_z_matrix = MatrixManager(width, height)
    	index_list = [0, 1, 1, 0]
    	self.sigma_z_matrix.set_index_list(0, index_list)
    	index_list = [0, 0, 1, 1]
    	self.sigma_z_matrix.set_index_list(self.position_noise**2, index_list)
    	# self.sigma_z_matrix.print_matrix()

    def init_mu_t_matrix(self):
    	width = 1
    	height = 6
    	self.mu_t_matrix = MatrixManager(width, height)
    	self.mu_t_matrix.set_all_values(0)
    	# self.mu_t_matrix.print_matrix()

    def init_sigma_t_matrix(self):
    	self.init_sigma_t_matrix
    	width = 6
    	height = 6
    	self.sigma_t_matrix = MatrixManager(width, height)
    	self.sigma_t_matrix.set_all_values(0)
    	index_list = [0, 0, 3, 3]
    	self.sigma_t_matrix.set_index_list(self.position_variance, index_list)
    	index_list = [1, 1, 4, 4]
    	self.sigma_t_matrix.set_index_list(self.velocity_variance, index_list)
    	index_list = [2, 2, 5, 5]
    	self.sigma_t_matrix.set_index_list(self.acceleration_variance, index_list)
    	# self.sigma_t_matrix.print_matrix()

    #	Note also that the expression (F(sigma-t)FT + sigma-x) occurs three times in the equations, so you may save some time by calculating that first.
    def common_computation(self):
    	temp_matrix_one = numpy.dot(self.f_matrix.values, self.sigma_t_matrix.values)
    	temp_matrix_two = numpy.dot(temp_matrix_one, self.transpose_f_matrix.values)
    	return temp_matrix_two + self.sigma_x_matrix.values

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
    # bzrc = BZRC(host, int(port))
    # agent = KalmanTank(bzrc, 0, True, "green")
    agent = KalmanTank(None, 0, True, "green")
    # agent.play()


if __name__ == '__main__':
    main()




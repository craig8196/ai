from __future__ import division
import sys
import math
import time
import random
from bzrc import BZRC, Command
from potential_fields import *
from env import EnvironmentState 

class Tank(object):
	def __init__(self, bzrc, index, debug, color):
		self.bzrc = bzrc
		self.index = index
		self.debug = debug
		self.prev_time = time.time()
		self.color = color

	def play(self):
		try:
			while True:
				time_diff = time.time() - self.prev_time
				self.tick(time_diff)
		except KeyboardInterrupt:
			print "Exiting due to keyboard interrupt."
			self.bzrc.close()
			exit(0)

	def tick(self, time_diff):
	    """Get a new state."""
	    env_state = self.bzrc.get_environment_state(self.color)
	    mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
	    self.mytanks = mytanks
	    self.othertanks = othertanks
	    self.flags = flags
	    self.shots = shots
	    self.time_diff = time_diff
	    commands = self.behave(time_diff, env_state)
	    self.bzrc.do_commands(commands)
	    # print "Updated "+str(time_diff)

	def behave(self, time_diff, env_state):
		pass

	def normalize_angle(self, angle):
	    """Make any angle be between +/- pi."""
	    angle -= 2 * math.pi * int (angle / (2 * math.pi))
	    if angle <= -math.pi:
	        angle += 2 * math.pi
	    elif angle > math.pi:
	        angle -= 2 * math.pi
	    return angle

	#general movement functions
	def move_forward(self, shoot):
		return Command(self.index, 1, 0, shoot)

	def move_backward(self, shoot):
		return Command(self,index, -1, 0, shoot)

	def move_to_position(self, tank, target_x, target_y):
	    """Set command to move to given coordinates."""
	    target_angle = math.atan2(target_y - tank.y,
	                              target_x - tank.x)
	    relative_angle = self.normalize_angle(target_angle - tank.angle)
	    return Command(tank.index, 1, 2 * relative_angle, True)

	def aim(self, tank, target_x, target_y):
		target_angle = math.atan2(target_y - tank.y,
	                              target_x - tank.x)
		relative_angle = self.normalize_angle(target_angle - tank.angle)
		return Command(tank.index, 0, 2.5 * relative_angle, True)
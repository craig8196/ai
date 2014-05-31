from __future__ import division
import sys
import math
import time
import random
from bzrc import BZRC, Command
from potential_fields import *
from env import EnvironmentState
from base_tank import Tank

class WildAgent(Tank):
    def __init__(self, bzrc, index, debug, color):
        super(WildAgent, self).__init__(bzrc, index, debug, color)
        self.last_time_goal_set = time.time() - self.prev_time
        self.time_interval = random.uniform(4, 11)
        self.destination_x = 0
        self.destination_y = 0
        self.destination_r = 0
        self.destination_s = 100
        self.attractive_constant = 1.25
        if self.debug:
            self.print_current_destination()

    def new_attractive_field(self, time_diff):
        self.destination_x = random.randint(-400, 400)
        self.destination_y = random.randint(-400, 400)
        self.time_interval = random.uniform(2, 11)
        self.last_time_goal_set = time_diff
        if self.debug:
            self.print_current_destination()

    def print_current_destination(self):
        print("destination x: " + str(self.destination_x))
        print("destination y: " + str(self.destination_y))

    def behave(self, time_diff, env_state):
        mytank = env_state.get_mytank(self.index)
        commands = []

        bag_o_fields = []

        if (time_diff - self.last_time_goal_set) > self.time_interval:
            self.new_attractive_field(time_diff)

        bag_o_fields.append(make_circle_attraction_function(self.destination_y, self.destination_y, self.destination_r, self.destination_s, self.attractive_constant))

        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(mytank.x, mytank.y)
        commands.append(self.move_to_position(mytank, mytank.x + dx, mytank.y + dy))
        return commands

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
    agent = WildAgent(bzrc, 0, True, "purple")
    agent.play()

if __name__ == '__main__':
    main()

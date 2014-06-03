#!/usr/bin/python -tt

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
#
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
#
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

import sys
import math
import time
import random
from Gnuplot import GnuplotProcess

from bzrc import BZRC, Command
from potential_fields import *

class ConformingAgent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_environment_constants()
        self.commands = []
        self.last_goal_switch = -20
        self.goal = (0, 0)

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        
        self.commands = []
        
        for tank in mytanks:
            self.behave(tank, time_diff)

        results = self.bzrc.do_commands(self.commands)
    
    def behave(self, tank, time_diff):
        """Move in one direction.
        """
        bag_o_fields = []
        
        if time_diff - self.last_goal_switch > 20:
            self.last_goal_switch = time_diff
            size = self.constants.worldsize
            self.goal = (random.randint(int(-size), int(size)),
                         random.randint(int(-size), int(size)))
        
        f = make_circle_attraction_function(self.goal[0], self.goal[1], 1, self.constants.worldsize, 2)
        bag_o_fields.append(f)
        
        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(tank.x, tank.y)
        command = self.move_to_position(tank, tank.x + dx, tank.y + dy, False)
        self.commands.append(command)
    
    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def move_to_position(self, tank, target_x, target_y, shoot=True):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        return Command(tank.index, 1, 2 * relative_angle, shoot)
        

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

    agent = ConformingAgent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

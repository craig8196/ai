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
from Gnuplot import GnuplotProcess

from bzrc import BZRC, Command
from potential_fields import *

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.tanks = {}
        self.bases = bzrc.get_bases()
        for base in self.bases:
            if base.color == self.constants['team']:
                self.base = base
        
        self.WORLDSIZE = int(self.constants['worldsize'])
        
        self.gp = GnuplotProcess(persist=False)
        self.gp.write(gnuplot_header(-self.WORLDSIZE / 2, self.WORLDSIZE / 2))

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]
        
        self.commands = []
        
        for tank in mytanks:
            if tank.index == 0:
                self.behave(tank, time_diff)
            else:
                self.behave(tank, time_diff)

        results = self.bzrc.do_commands(self.commands)

    def closest_flag(self, flags, tank, flags_captured):
        closest_dist = sys.maxint
        chosen_flag = flags[0]
        for flag in flags:
            distance = compute_distance(flag.x, tank.x, flag.y, tank.y)
            if distance < closest_dist and not flags_captured.__contains__(flag.color):
                closest_dist = distance
                chosen_flag = flag 
        return chosen_flag
    
    def behave(self, tank, time_diff, plot=False):
        """Create a behavior command based on potential fields.
        Plot the potential field if plot is True.
        """
        bag_o_fields = []
        # avoid enemies
        for enemy in self.enemies:
            if enemy.status == self.constants['tankalive']:
                bag_o_fields.append(make_circle_repulsion_function(enemy.x, enemy.y, int(self.constants['tanklength']), int(self.constants['tanklength'])*5))
        
        # avoid shots
        for shot in self.shots:
            bag_o_fields.append(make_circle_repulsion_function(shot.x, shot.y, int(self.constants['tanklength']), int(self.constants['tanklength'])*3))

        enemy_flags = []
        for flag in self.flags:
            if flag.color != self.constants['team']:
                enemy_flags.append(flag)
            else:
                our_flag = flag

        #if another tank on your team has a flag, that tank becomes a tangential field
        #also, make sure that any flag that a teammate is carrying is no longer attractive
        flags_captured = []
        for my_tank in self.mytanks:
            if my_tank != tank and my_tank.flag != "-":
                bag_o_fields.append(make_tangential_function(my_tank.x, my_tank.y, int(self.constants['tanklength']), 80, 1, 4))
                flags_captured.append(my_tank.flag)

        #if an enemy tank has captured our flag, they become a priority
        public_enemy = None
        for other_tank in self.othertanks:
            if other_tank.flag == self.constants['team']:
                public_enemy = other_tank

        if tank.flag != "-":
            goal = self.base 
            cr = (self.base.corner1_x - self.base.corner2_x) / 2
            goal.x = self.base.corner1_x + cr
            goal.y = self.base.corner1_y + cr
            cs = 10
            a = 2
        elif public_enemy is not None:
            goal = public_enemy
            cr = int(self.constants['tanklength'])
            cs = 20
            a = 3
        else:
            goal = self.closest_flag(enemy_flags, tank, flags_captured)
            cr = 2
            cs = 20
            a = 2
        bag_o_fields.append(make_circle_attraction_function(goal.x, goal.y, cr, cs, a))

        
        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(tank.x, tank.y)
        self.move_to_position(tank, tank.x + dx, tank.y + dy)
        
        if plot:
            self.gp.write(plot_field(pfield_function))
    
    def attack_enemies(self, tank):
        """Find the closest enemy and chase it, shooting as you go."""
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        for enemy in self.enemies:
            if enemy.status != 'alive':
                continue
            dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy
        if best_enemy is None:
            command = Command(tank.index, 0, 0, False)
            self.commands.append(command)
        else:
            self.move_to_position(tank, best_enemy.x, best_enemy.y)

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, True)
        self.commands.append(command)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

class Tank(object):
    """Just a class to hold fields."""
    pass

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

    agent = Agent(bzrc)

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

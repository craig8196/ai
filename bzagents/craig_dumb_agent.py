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
from __future__ import division

import sys
import math
import time
import random

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        print self.constants
        self.tanks = {}

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
            if not tank.index in self.tanks:
                self.tanks[tank.index] = {
                    'speed': 1,
                    'start_turn': False,
                    'start_forward': 0,
                    'forward_len': random.uniform(3, 8),
                    'prev_shot': 0,
                    'shot_len': 0,
                    'shoot': False,
                    'angvel': 0,
                    'target_angle': tank.angle,
                    'turning': False,
                }
            self.act_dumb(tank, time_diff)

        results = self.bzrc.do_commands(self.commands)
        self.prev_time = time_diff
    
    def act_dumb(self, tank, time_diff):
        """Make the given tank act dumb."""
        data = self.tanks[tank.index]
        if time_diff - data['start_forward'] > data['forward_len']:
            data['speed'] = 0
            data['start_turn'] = True
            data['start_forward'] = time_diff
            
        
        sixty_deg_in_radians = 60/180*math.pi
        
        if data['start_turn']:
            l_or_r = random.randint(0, 1)
            if l_or_r == 0:
                direction = -1
            else:
                direction = 1
            data['start_angle'] = self.normalize_angle(tank.angle)
            data['target_angle'] = self.normalize_angle(tank.angle + direction*sixty_deg_in_radians)
            data['start_turn'] = False
            data['angvel'] = direction*1.0
            data['turning'] = True
        
        if data['turning']:
            if self.min_angle_between(data['target_angle'], tank.angle) > sixty_deg_in_radians:
                data['turning'] = False
                data['angvel'] = 0
                data['forward_len'] = random.uniform(3, 8)
                data['start_forward'] = time_diff
                data['speed'] = 1
                #~ print self.min_angle_between(data['target_angle'], tank.angle)
        
        if time_diff - data['prev_shot'] > data['shot_len']:
            data['shoot'] = True
            data['prev_shot'] = time_diff
            data['shot_len'] = random.uniform(1.5, 2.5)
        
        command = Command(tank.index, data['speed'], data['angvel'], data['shoot'])
        self.commands.append(command)        
    
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
    
    def min_angle_between(self, angle1, angle2):
        """Inputs must be normalized.
        Return the minimal positive angle between the given angles.
        """
        diff = math.fabs(angle1 - angle2)
        if diff > math.pi:
            diff = 2*math.pi - diff
        return diff
    
    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle


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

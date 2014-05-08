import sys
import math
import time
import random

from bzrc import BZRC, Command

class DumbTank(object):

    def __init__(self, bzrc, index):
        self.bzrc = bzrc
        self.agent = DumbAgent(bzrc, index)
    
    def tick(self, time_diff):
        self.agent.tick(time_diff)

class DumbAgent(object):

    def __init__(self, bzrc, index):
        self.bzrc = bzrc
        self.index = index
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.time_shooting_elapsed = 0
        self.time_moving_elapsed = 0
        self.random_shooting_interval = random.uniform(1.5, 2.5)
        self.random_moving_forward_interval = random.uniform(3, 8)
        self.is_turning = False
        
    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.tank = mytanks[self.index]
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []
        shoot = self.check_for_shooting

        if self.is_turning or self.stop_moving_forward(time_diff):
            self.is_turning = self.turn_counter_clockwise(self.target_angle, shoot)
        else:
            self.move_forward(shoot)

        results = self.bzrc.do_commands(self.commands)
        
    def check_for_shooting(self, time_diff):
        self.time_shooting_elapsed += time_diff
        if self.time_shooting_elapsed >= self.random_shooting_interval:
            self.random_shooting_interval = random.uniform(1.5, 2.5)
            self.time_shooting_elapsed = 0
            return True
        else:
            return False
            
    def stop_moving_forward(self, time_diff):
        self.time_moving_elapsed += time_diff
        if self.time_moving_elapsed >= self.random_moving_forward_interval:
            self.random_moving_forward_interval = random.uniform(3, 8)
            self.time_moving_elapsed = 0
            self.target_angle = self.tank.angle + (math.pi / 3)
            self.is_turning
            return True
        else:
            return False
        
    def move_forward(self, shoot):
        command = Command(self.index, 1, 0, shoot)
        self.commands.append(command)

    def turn_counter_clockwise(self, target_angle, shoot):
        relative_angle = self.normalize_angle(target_angle - self.tank.angle)
        command = Command(self.index, 0, 2 * relative_angle, shoot)
        self.commands.append(command)
        if relative_angle < 0.1:
            return False
        else:
            return True
        
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

    tanks = bzrc.get_tanks()
    dumb_tanks = []
    for tank in tanks:
        t = DumbTank(bzrc, tank.index)
        dumb_tanks.append()

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            prev_time = time.time()
            for dumb in dumb_tanks:
                dumb.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()
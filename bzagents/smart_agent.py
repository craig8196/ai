import sys
import math
import time
import random

from bzrc import BZRC, Command

class SmartTank(object):

    def __init__(self, tank):
        self.changein_x = 0
        self.changein_y = 0
        self.tank = tank
        self.shoot = False

    def update_tank(tank):
        self.tank = tank

    def get_x():
        return self.tank.x

    def get_y():
        return self.tank.y

    def get_index():
        return self.tank.index

    def get_speed():
        pass

    def get_angvel():
        pass

    def get_shoot():
        return self.shoot

    def change_vectors(x, y):
        self.changein_x = x
        self.changein_y = y

class AttractiveField(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.inner_radius = 2
        self.field_radius = 200

    def compute_distance(x, y):
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)

    def compute_angle(x, y):
        return math.atan2((self.y - y)/(self.x - x))

    def generate_field(self, tank_x, tank_y):
        angle = compute_angle(tank_x, tank_y)
        distance = compute_distance(tank_x, tank_y)
        a = 4 
        if distance < self.inner_radius:
            return [0, 0]
        elif distance <= (self.inner_radius + self.field_radius):
            return [a * (distance - self.radius) * math.cos(angle), a * (distance - self.radius) * math.sin(angle)] 
        else:
            return [a * self.field_radius * math.cos(angle), a * self.field_radius * math.sin(angle)] 



class SmartAgent(object):

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
        self.my_smart_tanks = []
        mytanks = self.bzrc.read_mytanks()
        for tank in mytanks:
            smart_tank = SmartTank(tank)
            self.my_smart_tanks << smart_tank

        
    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.shots = shots
        for smart_tank in self.my_smart_tanks:
            smart_tank.update_tank(mytanks[smart_tank.index])
        self.flags = flags
        self.attractive_fields = []
        for flag in flags:
            if flag.color != self.constants['team']:
                field = AttractiveField(flag.x, flag.y)
                self.attractive_fields << field

        self.commands = []
        for smart_tank in self.my_smart_tanks:
            min_distance = sys.maxint
            for field in self.attractive_fields:

        shoot = self.check_for_shooting

        if self.is_turning or self.stop_moving_forward(time_diff):
            self.is_turning = self.turn_counter_clockwise(self.target_angle, shoot)
        else:
            self.move_forward(shoot)

        for smart_tank in self.my_smart_tanks:
            command = Command(smart_tank.get_index(), smart_tank.get_speed(), smart_tank.get_angvel(), smart_tank.get_shoot())
            self.commands.append(Command)

        results = self.bzrc.do_commands(self.commands)
        
    def check_for_shooting(self, time_diff):
        self.time_shooting_elapsed += time_diff
        if self.time_shooting_elapsed >= self.random_shooting_interval:
            self.random_shooting_interval = random.uniform(1.5, 2.5)
            self.time_shooting_elapsed = 0
            return True
        else:
            return False

    def attract_field(self, ):
            
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

    tank0 = DumbTank(bzrc, 0)
    tank1 = DumbTank(bzrc, 1)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            prev_time = time.time()
            tank0.tick(time_diff)
            tank1.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()
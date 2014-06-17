#!/usr/bin/python -tt
#################################################################
# python pfield_team_agent.py [hostname] [port]
#################################################################
from __future__ import division
import sys
import math
import time
import random
from threading import Thread, Event
from bzrc import BZRC, Command
from potential_fields import *
from utilities import ThreadSafeQueue
from graph import PotentialFieldGraph
from env import EnvironmentState
from threading import Thread, Lock, Event

class TeamManager(object):

    """Handle all command and control logic for a team of tanks."""
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.env_constants = self.bzrc.get_environment_constants()
        self.tanks = []
        self.corners = []
        for i in range(0, int(self.env_constants.get_count(self.env_constants.color))):
            self.tanks.append(PFieldTank(i, self.bzrc, self.corners, self.env_constants))
        for tank in self.tanks:
            tank.setDaemon(True)
            tank.start()

    def play(self):
        """Start playing BZFlag!"""
        # try:
        #     import _tkinter
        #     import Tkinter
        #     from bzui import BZUI
        #     ui = BZUI(self.tanks, self.env_constants)
        #     ui.setDaemon(True)
        #     ui.start()
        # except ImportError:
        #     print "You need Tkinter to be installed to use the graphical interface."
        
        prev_time = time.time()
        # Continuously get the environment state and have each tank update
        try:
            while True:
                time_diff = time.time() - prev_time
                self.tick(time_diff)
        except KeyboardInterrupt:
            print "Exiting due to keyboard interrupt."
            self.bzrc.close()
            exit(0)
    
    def tick(self, time_diff):
        """Get a new state."""
        env_state = self.bzrc.get_environment_state(self.env_constants.color)
        env_state.time_diff = time_diff
        for tank in self.tanks:
            tank.add_env_state(env_state)
        commands = []
        for tank in self.tanks:
            tank.signal_done_updating.wait()
            #~ tank.behave(env_state)
            commands.append(tank.command)
        self.bzrc.do_commands(commands)
        # print "Updated "+str(time_diff)


class PFieldTank(Thread):
    """Handle all command and control logic for a single tank."""
    
    def __init__(self, index, bzrc, corners, env_constants):
        """The brain must take in a state and produce a command."""
        super(PFieldTank, self).__init__()
        self.index = index # same as tank id
        self.cg = CommandGenerator()
        self.bzrc = bzrc
        self.error = 0
        self.env_states = ThreadSafeQueue()
        self.env_constants = env_constants
        self.our_base = None
        self.all_initialized = False

        self.keep_running = True
        self.graph = None
        self.last_sensor_poll = -1.0
        self.exploration_goal = (0, 0)
        self.past_places = {}
        self.signal_new_env = Event()
        self.signal_new_env.clear()
        self.signal_done_updating = Event()
        self.signal_done_updating.clear()
        self.command = None

        self.behaviors = []
        self.behavior = None
        self.ourbase_center_y = 0
        self.ourbase_center_x = 0
            
    def stop(self):
        self.keep_running = False

    def initialize_states(self):
        self.last_time_moved = self.env_state.time_diff
        mytank = self.env_state.mytanks[self.index]
        self.prev_x = mytank.x
        self.prev_y = mytank.y

        self.color = self.env_constants.color

        for base in self.env_constants.bases:
            if base.color == self.color:
                self.our_base = base

        self.ourbase_center_y = (self.our_base.corner3_y + self.our_base.corner1_y) / 2.0
        self.ourbase_center_x = (self.our_base.corner2_x + self.our_base.corner1_x) / 2.0
    
    def add_env_state(self, env_state):
        self.env_state = env_state
        self.signal_done_updating.clear()
        self.signal_new_env.set()
        if not self.all_initialized:
            self.initialize_states()
            self.all_initialized = True

    def update_behaviors(self):
        if not self.behaviors:
            self.init_behaviors()
            self.update_existing_behaviors()
        else:
            self.update_existing_behaviors()

    def init_behaviors(self):
        self.mytank = self.env_state.mytanks[self.index]

        #create the behaviors for capturing enemy flags
        for i, enemyflag in enumerate(self.env_state.enemyflags):
            self.behaviors.append(SeekGoalBehavior("flag" + enemyflag.color, self.mytank, 350, 3, 0.3, self.env_constants.color, i))

        #create the behavior for bringing a captured flag back to our base
        self.behaviors.append(SeekGoalBehavior("base", self.mytank, 450, 5, 0.3, self.env_constants.color, -1))

        #create the behaviors for shooting an enemy tank
        for enemytank in self.env_state.enemytanks:
            self.behaviors.append(DestroyEnemyBehavior("enemytank", self.mytank, 280, 6, 0.3))

        #create the behavior for getting unstuck
        self.behaviors.append(GetUnstuckBehavior("unstuck", self.mytank, 600, 5, 0.3))

    def update_existing_behaviors(self):
        self.mytank = self.env_state.mytanks[self.index]
        curr_time = self.env_state.time_diff
        enemy_index = 0
        for behavior in self.behaviors:
            if type(behavior) is DestroyEnemyBehavior:
                enemy_tank = self.env_state.enemytanks[enemy_index]
                behavior.update(self.mytank, curr_time, enemy_tank.x, enemy_tank.y)
                enemy_index += 1
            elif type(behavior) is SeekGoalBehavior:
                if 'flag' in behavior.identifier:
                    for flag in self.env_state.enemyflags:
                        if flag.color in behavior.identifier:
                            enemy_flag = flag
                    behavior.update(self.mytank, curr_time, enemy_flag.x, enemy_flag.y)
                else:
                    behavior.update(self.mytank, curr_time, self.ourbase_center_x, self.ourbase_center_y)
            elif type(behavior) is GetUnstuckBehavior:
                behavior.update(self.mytank, curr_time, self.mytank.x, self.mytank.y)
    
    def remove_env_state(self):
        self.signal_new_env.wait()
        self.signal_new_env.clear()
        return self.env_state
    
    def run(self):
        while self.keep_running:
            s = self.remove_env_state()
            if self.keep_running:
                self.behave(s)
                self.signal_done_updating.set()

    def get_most_useful_behavior(self):
        curr_max = -sys.maxint
        best_behavior = self.behaviors[0]
        for b in self.behaviors:
            if type(b) is DestroyEnemyBehavior:
                value = b.evaluate_utility(self.env_state.myflag)
            elif type(b) is SeekGoalBehavior:
                value = b.evaluate_utility(self.env_state.enemyflags[b.flag_index].poss_color)
            elif type(b) is GetUnstuckBehavior:
                value = b.evaluate_utility(self.env_state.time_diff - self.last_time_moved)
            if value >= curr_max:
                curr_max = value
                best_behavior = b
        return max, best_behavior

    def check_if_moved(self, x, y, curr_time):
        if abs(self.prev_x - x) >= 7 or abs(self.prev_y - y) >= 7:
            self.prev_x = x
            self.prev_y = y
            self.last_time_moved = curr_time

    def behave(self, env_state):
        self.update_behaviors()
        if self.behavior:
            print self.behavior.identifier
        mytank = env_state.mytanks[self.index]
        self.check_if_moved(mytank.x, mytank.y, env_state.time_diff)

        if not self.behavior:
            (value, behavior) = self.get_most_useful_behavior()
            self.behavior = behavior
            self.behavior.last_use_start_time = env_state.time_diff
        else:
            if env_state.time_diff - self.behavior.last_use_start_time >= self.behavior.min_time:
                (value, behavior) = self.get_most_useful_behavior()
                self.behavior = behavior
                self.behavior.last_use_start_time = env_state.time_diff

        self.command = self.behavior.behave()

class Behavior(object):
    def __init__(self, name, tank, priority_value, min_time, update_frequency):
        self.cg = CommandGenerator()
        self.th = TankHelper()
        self.identifier = name
        self.mytank = tank
        self.priority_value = priority_value
        self.min_time = min_time
        self.update_frequency = update_frequency
        self.last_time_updated = 0
        self.last_use_start_time = 0
        self.target_x = 0
        self.target_y = 0
        self.current_distance = self.th.get_distance(self.mytank.x, self.mytank.y, self.target_x, self.target_y)

    def update(self, tank, curr_time, x, y):
        if curr_time - self.last_time_updated >= self.update_frequency:
            self.last_time_updated = curr_time
            self.mytank = tank
            self.target_x = x
            self.target_y = y
            self.current_distance = self.th.get_distance(self.mytank.x, self.mytank.y, self.target_x, self.target_y)

    def evaluate_utility(self, modifier):
        pass

    def behave():
        pass

class DestroyEnemyBehavior(Behavior):
    def __init__(self, name, tank, priority_value, min_time, update_frequency):
        super(DestroyEnemyBehavior, self).__init__(name, tank, priority_value, min_time, update_frequency)

    def evaluate_utility(self, modifier):
        #in this case, the modifier would be the position of our flag
        #so, if the enemy is really close to or has our flag, give this higher priority
        if self.current_distance == 0:
            return 0
        elif self.th.get_distance(self.target_x, modifier.x, self.target_y, modifier.y) < 10:
            return self.priority_value * 3 * (1.0 / self.current_distance)
        elif self.current_distance < 90:
            return self.priority_value * (1.0 / self.current_distance)
        else:
            return 0

    def behave(self):
        fire_dist = self.th.get_distance(self.mytank.x, self.mytank.y, self.target_x, self.target_y)
        fire_angle = math.atan2(self.target_y - self.mytank.y, self.target_x - self.mytank.x)
        if abs(5.0 / fire_dist) <= 1:
            fire_delta = abs(5.0 / fire_dist)
        else:
            fire_delta = 0

        if abs(fire_angle - self.mytank.angle) < fire_delta and fire_dist <= 350:
            fire = True
        else:
            fire = False
        
        angvel = 2*self.th.normalize_angle(fire_angle - self.mytank.angle)
        
        return Command(self.mytank.index, 0.3, angvel, fire)

class SeekGoalBehavior(Behavior):
    def __init__(self, name, tank, priority_value, min_time, update_frequency, color, flag_index):
        super(SeekGoalBehavior, self).__init__(name, tank, priority_value, min_time, update_frequency)
        self.pf = PotentialFields()
        self.color = color
        self.flag_index = flag_index

    def evaluate_utility(self, modifier):
        #it is a flag goal
        if 'flag' in self.identifier:
            if modifier == self.color:
                return 0
            elif self.current_distance == 0:
                return 0
            else:
                return self.priority_value * (1.0 / self.current_distance)

        #it is a take the flag back to base goal
        else:
            if self.current_distance == 0:
                return 0
            elif self.mytank.flag != '-' and self.mytank.flag != self.color:
                return self.priority_value * (1.0 / self.current_distance)
            else:
                return 0 

    def behave(self):
        bag_o_fields = []
        bag_o_fields.append(self.pf.make_circle_attraction_function(self.target_x, self.target_y, 2, 20, 2))

        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(self.mytank.x, self.mytank.y)

        return self.cg.move_to_position(self.mytank, self.mytank.x + dx, self.mytank.y + dy)

class GetUnstuckBehavior(Behavior):
    def __init__(self, name, tank, priority_value, min_time, update_frequency):
        super(GetUnstuckBehavior, self).__init__(name, tank, priority_value, min_time, update_frequency)
        self.pf = PotentialFields()

    def evaluate_utility(self, modifier):
        #in this case, the modifier is how long ago the last time the tank moved was
        if modifier < 2:
            return 0
        else:
            return self.priority_value

    def behave(self):
        bag_o_fields = []
        bag_o_fields.append(self.pf.make_circle_repulsion_function(self.target_x, self.target_y, 2, 20, 2))

        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(self.mytank.x, self.mytank.y)

        return Command(self.mytank.index, 0.8, 0.4, True)

        # return self.cg.move_to_position(self.mytank, self.mytank.x + dx, self.mytank.y + dy)        

class CommandGenerator(object):
    def __init__(self):
        self.varying_speeds_index = 0
        self.varying_speeds = [1.0, 0.9, 0.8, 0.7, 0.5, -1, -0.6]
        self.th = TankHelper()

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

        if self.th.get_distance(tank.x, tank.y, target_x, target_y) < 15:
            speed = 0.7
        else:
            speed = 1
        return Command(tank.index, speed, 2 * relative_angle, False)

    def move_to_position_varying_speed(self, tank, target_x, target_y, num_iterations):
        self.current_speed_iteration += 1
        if self.current_speed_iteration > num_iterations:
            if self.varying_speeds_index + 1 < len(self.varying_speeds):
                self.varying_speeds_index += 1
            else:
                self.varying_speeds_index = 0 
            self.current_speed_iteration = 0
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        return Command(tank.index, self.varying_speeds[self.varying_speeds_index], 2 * relative_angle, True)

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


    def aim(self, tank, target_x, target_y):
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        return Command(tank.index, 0, 2.5 * relative_angle, True)

class TankHelper(object):
    def __init__(self):
        pass

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def get_distance(self, x1, y1, x2, y2):
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

class PotentialFields(object):
    from numpy import linspace

    def __init__(self):
        pass

    # Vector math
    def length_squared(self, v1, v2):
        """Return |v1-v2|^2."""
        return (v1[0] - v2[0])**2 + (v1[1] - v2[1])**2

    def calc_distance(self, v1, v2):
        """Return distance between 2 tuples of length 2."""
        return math.sqrt(length_squared(v1, v2))

    def dot_product(self, v1, v2):
        """Return dot product of 2 tuples length 2."""
        return v1[0]*v2[0] + v1[1]*v2[1]

    def calc_vector(self, x1, y1, x2, y2, max_distance, angle):
        xdiff = x2 - x1
        ydiff = y2 - y1
        d = math.sqrt(xdiff**2 + ydiff**2)
        if d > max_distance:
            return 0, 0
        else:
            theta = math.atan2(ydiff, xdiff)
            theta += angle*math.pi/180
            dx = ((max_distance - d)/max_distance)*math.cos(theta)
            dy = ((max_distance - d)/max_distance)*math.sin(theta)
            return dx, dy

    def compute_distance(self, cx, x, cy, y):
        return math.sqrt((cx - x)**2 + (cy - y)**2)


    def compute_angle(self, cx, x, cy, y):
        return math.atan2((cy - y), (cx - x))

    def make_circle_attraction_function(self, cx, cy, cr, cs, a):
        """cx, cy define center, cr is radius, cs is outer radius"""
        def circle_attraction_field(x, y):
            distance = compute_distance(cx, x, cy, y)
            theta = compute_angle(cx, x, cy, y)
            #~ if distance < cr:
                #~ return 0, 0
            #~ elif distance <= (cr + cs):
                #~ return [a * (distance - cr) * math.cos(theta), a * (distance - cr) * math.sin(theta)] 
            #~ else:
                #~ return [a * cs * math.cos(theta), a * cs * math.sin(theta)] 
            if distance < cr:
                return 0, 0
            elif distance > cs:
                return a*math.cos(theta), a*math.sin(theta)
            else:
                max_dist = cs - cr
                dist_to_edge = distance - cr
                dx = (dist_to_edge/max_dist)*math.cos(theta)
                dy = (dist_to_edge/max_dist)*math.sin(theta)
                return a * dx, a * dy
        return circle_attraction_field


    def make_circle_repulsion_function(self, cx, cy, cr, cs, a):
        """cx, cy define center, cr is radius, cs is outer radius"""
        def circle_repulsion_field(x, y):
            xdiff = cx - x
            ydiff = cy - y
            
            distance = math.sqrt(xdiff**2 + ydiff**2)
            theta = math.atan2(ydiff, xdiff)
            
            if distance < cr:
                return a * -math.cos(theta), a * -math.sin(theta)
            elif distance > cs:
                return 0, 0
            else:
                max_dist = cs - cr
                dist_to_edge = cs - distance
                dx = -(dist_to_edge/max_dist)*math.cos(theta)
                dy = -(dist_to_edge/max_dist)*math.sin(theta)
                return a * dx, a * dy
        return circle_repulsion_field


    def make_tangential_function(self, cx, cy, cr, cs, d, a):
        """cx, cy define center, cr is radius, cs is outer radius, d is -1 for counterclockwise and 1 for clockwise"""
        def tangential_function(x, y):
            xdiff = cx - x
            ydiff = cy - y
            distance = math.sqrt(xdiff**2 + ydiff**2)
            theta = math.atan2(ydiff, xdiff)
            theta += d*math.pi/2
            a = 4
            if distance < cr or distance > cs:
                return 0, 0
            else:
                dx = 4 * math.cos(theta)
                dy = 4 * math.sin(theta)
                return a *dx, a * dy
        return tangential_function

    def make_line_function(self, x1, y1, x2, y2, max_distance=10, angle=180):
        """x1, y1 and x2, y2 are the start and end points of the line.
        Return a function.
        """
        def line_field(x, y):
            len_sqrd = length_squared((x1, y1), (x2, y2))
            if len_sqrd == 0.0:
                return calc_vector(x, y, x1, y1, max_distance, angle)
            t = dot_product((x - x1, y - x1), (x2 - x1, y2 - y1)) / len_sqrd
            if t < 0.0:
                return calc_vector(x, y, x1, y1, max_distance, angle)
            elif t > 1.0:
                return calc_vector(x, y, x2, y2, max_distance, angle)
            else:
                newx = x1 + t*(x2 - x1)
                newy = y1 + t*(y2 - y1)
                return calc_vector(x, y, newx, newy, max_distance, angle)
        return line_field

    def random_field(self, x, y):
        magnitude = random.uniform(0, 1)
        theta = random.uniform(0, 2*math.pi)
        return magnitude*math.cos(theta), magnitude*math.sin(theta)

class Container(object):
    def __init__(self):
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


    team = TeamManager(bzrc)
    # Corners.init_corners_not_yet_targeted(bzrc)
    team.play()


if __name__ == '__main__':
    main()

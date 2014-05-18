#!/usr/bin/python -tt
#################################################################
# python pfield_team_agent.py [hostname] [port]
#################################################################

import sys
import math
import time
import random
from threading import Thread
from bzrc import BZRC, Command
from potential_fields import *
from utilities import ThreadSafeQueue
from graph import PotentialFieldGraph
from env import EnvironmentState


class TeamManager(object):

    """Handle all command and control logic for a team of tanks."""
    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.env_constants = self.bzrc.get_environment_constants()
        self.tanks = []
        for i in range(0, int(self.env_constants.get_count(self.env_constants.color))):
            self.tanks.append(PFieldTank(i, self.bzrc, self.env_constants))
        for tank in self.tanks:
            tank.setDaemon(True)
            tank.start()

    @classmethod
    def init_corners_not_yet_targeted(cls):
        cls.corners_not_yet_targeted = []

        top_left_corner = Answer()
        top_left_corner.x = 0
        top_left_corner.y = 0
        cls.corners_not_yet_targeted.append(top_left_corner)

        bottom_left_corner = Answer()
        bottom_left_corner.x = 0
        bottom_left_corner.y = self.env_constants.worldsize
        cls.corners_not_yet_targeted.append(bottom_left_corner)

        top_right_corner = Answer()
        top_right_corner.x = self.env_constants.worldsize
        top_right_corner.y = 0
        cls.corners_not_yet_targeted.append(top_right_corner)

        bottom_right_corner = Answer()
        bottom_right_corner.x = self.env_constants.worldsize
        bottom_right_corner.y = self.env_constants.worldsize
        cls.corners_not_yet_targeted.append(bottom_right_corner)
    
    def play(self):
        """Start playing BZFlag!"""
        try:
            import _tkinter
            import Tkinter
            from bzui import BZUI
            ui = BZUI(self.tanks, self.env_constants)
            ui.setDaemon(True)
            ui.start()
        except ImportError:
            print "You need Tkinter to be installed to use the graphical interface."
        
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
        env_state = self.bzrc.get_environment_state(self.env_constants.color, )
        env_state.time_diff = time_diff
        for tank in self.tanks:
            tank.add_env_state(env_state)    

class PFieldTank(Thread):
    """Handle all command and control logic for a single tank."""
    
    def __init__(self, index, bzrc, env_constants):
        """The brain must take in a state and produce a command."""
        super(PFieldTank, self).__init__()
        self.index = index # same as tank id
        self.bzrc = bzrc
        self.error = 0
        self.env_states = ThreadSafeQueue()
        self.env_constants = env_constants
        self.keep_running = True
        self.graph = None
        self.last_sensor_poll = -1.0
        self.exploration_goal = (0, 0)
        self.past_places = {}
    
    def start_plotting(self):
        if not self.graph:
            self.graph = PotentialFieldGraph(self.env_constants.worldsize)
            self.graph.setDaemon(True)
            self.graph.start()
    
    def stop_plotting(self):
        if self.graph:
            self.graph.stop()
    
    def is_plotting(self):
        if self.graph:
            return True
        return False
            
    def stop(self):
        self.keep_running = False
    
    def add_env_state(self, env_state):
        self.env_states.add(env_state)
    
    def remove_env_state(self):
        result = self.env_states.remove()
        while len(self.env_states) > 0:
            result = self.env_states.remove()
        return result
    
    def run(self):
        while self.keep_running:
            s = self.remove_env_state()
            if self.keep_running:
                self.behave(s)

    def closest_object_in_a_list(self, tank, obj_list):
        closest_dist = sys.maxint
        chosen_object = obj_list[0]
        return chosen_object
        for obj in obj_list:
            distance = compute_distance(obj.x, tank.x, obj.y, tank.y)
            if distance < closest_dist:
                closest_dist = distance
                chosen_object = obj
        return chosen_object
    
    def closest_flag(self, flags, tank, flags_captured):
        closest_dist = sys.maxint
        chosen_flag = flags[0]
        for flag in flags:
            distance = compute_distance(flag.x, tank.x, flag.y, tank.y)
            if distance < closest_dist and not flags_captured.__contains__(flag.color):
                closest_dist = distance
                chosen_flag = flag 
        return chosen_flag
    
    #~ def update_places(self, mytank, time_diff):
        #~ if len(self.past_places) > 20:
            #~ self.past_places.pop(0)
            #~ self.past_places_functions
    
    def behave(self, env_state):
        """Create a behavior command based on potential fields given an environment state."""
        env_constants = self.env_constants # shorten the name
        bag_o_fields = []
        bag_o_fields.extend(env_constants.get_obstacle_functions())
        mytank = env_state.get_mytank(self.index)
        
        # get sensor update every second
        if env_state.time_diff - self.last_sensor_poll > 1.0:
            self.last_sensor_poll = env_state.time_diff
            x, y, grid = self.bzrc.get_grid_as_matrix(self.index, env_constants.worldsize)
            env_constants.grid.update(x, y, grid)
        
        
        
        #~ x, y = self.exploration_goal
        #~ prob = env_constants.grid.get_item(x, y)
        #~ lb = env_constants.grid.not_obstacle_threshold
        #~ ub = env_constants.grid.obstacle_threshold
        #~ if prob < lb or prob > ub:
            #~ x = random.randint(0, env_constants.worldsize-1)
            #~ y = random.randint(0, env_constants.worldsize-1)
        #~ bag_o_fields.append(make_circle_attraction_function(x - env_constants.worldsize/2, y - env_constants.worldsize/2, 1, 100, 2))
        # avoid enemies
        #~ for enemy in env_state.enemytanks:
            #~ if enemy.status == self.env_constants.alive:
                #~ bag_o_fields.append(make_circle_repulsion_function(enemy.x, enemy.y, env_constants.tanklength, env_constants.tanklength*5, 2))

        
        # avoid shots
        #~ for shot in env_state.shots:
            #~ bag_o_fields.append(make_circle_repulsion_function(shot.x, shot.y, env_constants.tanklength, env_constants.tanklength*3, 2))

        enemy_flags = env_state.enemyflags
        flags_not_captured = enemy_flags
        # flags_captured = []
        #~ our_flag = env_state.myflag
#~ 
        #~ #if another tank on your team has a flag, that tank becomes a tangential field
        #~ #also, make sure that any flag that a teammate is carrying is no longer attractive
        for my_tank in env_state.mytanks:
            if my_tank != mytank and my_tank.flag != "-":
                # flags_captured.append(my_tank.flag)
                # bag_o_fields.append(make_tangential_function(my_tank.x, my_tank.y, env_constants.tanklength, 80, 1, 20))
                flags_not_captured.remove(my_tank.flag)

#~ 
        #~ #if an enemy tank has captured our flag, they become a priority
        #~ public_enemy = None
        #~ for other_tank in env_state.enemytanks:
            #~ if other_tank.flag == env_constants.color:
                #~ public_enemy = other_tank
#~ 
        #~ if tank.flag != "-":
            #~ goal = self.base 
            #~ cr = (self.base.corner1_x - self.base.corner2_x) / 2
            #~ goal.x = self.base.corner1_x + cr
            #~ goal.y = self.base.corner1_y + cr
            #~ cs = 10
            #~ a = 3
        #~ elif public_enemy is not None:
            #~ goal1 = public_enemy
            #~ goal2 = self.closest_flag(enemy_flags, tank, flags_captured)
            #~ dist_goal1 = compute_distance(goal1.x, tank.x, goal1.y, tank.y)
            #~ dist_goal2 = compute_distance(goal2.x, tank.x, goal2.y, tank.y)
            #~ if dist_goal1 < dist_goal2:
                #~ goal = goal1 
                #~ cr = int(env_constants.tanklength)
                #~ cs = 20
                #~ a = 3
            #~ else:
                #~ goal = goal2
                #~ cr = 2
                #~ cs = 20
                #~ a = 2
        #~ else:
        # goal = self.closest_flag(enemy_flags, mytank, flags_captured)
        # cr = 2
        # cs = 20
        # a = 2
        # bag_o_fields.append(make_circle_attraction_function(goal.x, goal.y, cr, cs, a))

        if len(flags_not_captured) > 0:
            goal = self.closest_object_in_a_list(mytank, flags_not_captured)
            # goal = self.closest_flag(enemy_flags, mytank, flags_captured)
        elif len(corners_not_yet_targeted) > 0:
            goal = self.closest_corner(mytank, TeamManager.corners_not_yet_targeted)
            TeamManager.corners_not_yet_targeted.remove(goal)
        else:
            goal = Answer()
            goal.x = env_constants.worldsize / 2
            goal.y = env_constants.worldsize / 2

        cr = 2
        cs = 20
        a = 20
        bag_o_fields.append(make_circle_attraction_function(goal.x, goal.y, cr, cs, a))
        
        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(mytank.x, mytank.y)

        self.move_to_position(mytank, my_tank.x + dx, my_tank.y + dy)
        if self.graph:
            self.graph.add_function(pfield_function)
    
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
        self.bzrc.do_commands([command])

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

    team = TeamManager(bzrc)
    team.play()

if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4

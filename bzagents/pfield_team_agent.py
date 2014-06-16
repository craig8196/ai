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
        self.env_constants = self.bzrc.get_environment_beliefs()
        self.tanks = []
        self.corners = []
        for i in range(0, int(self.env_constants.get_count(self.env_constants.color))):
            self.tanks.append(PFieldTank(i, self.bzrc, self.corners, self.env_constants))
        for tank in self.tanks:
            tank.setDaemon(True)
            tank.start()


        top_left_corner = Container()
        top_left_corner.x = 0   
        top_left_corner.y = 0
        self.corners.append(top_left_corner)


        bottom_left_corner = Container()
        bottom_left_corner.x = 0
        bottom_left_corner.y = self.env_constants.worldsize
        self.corners.append(bottom_left_corner)


        top_right_corner = Container()
        top_right_corner.x = self.env_constants.worldsize
        top_right_corner.y = 0
        self.corners.append(top_right_corner)


        bottom_right_corner = Container()
        bottom_right_corner.x = self.env_constants.worldsize
        bottom_right_corner.y = self.env_constants.worldsize
        self.corners.append(bottom_right_corner)


        # self.init_corners_not_yet_targeted()


    # def init_corners_not_yet_targeted(self):
    #     self.corners_not_yet_targeted = []


    #     top_left_corner = Container()
    #     top_left_corner.x = 0
    #     top_left_corner.y = 0
    #     self.corners_not_yet_targeted.append(top_left_corner)


    #     bottom_left_corner = Container()
    #     bottom_left_corner.x = 0
    #     bottom_left_corner.y = self.env_constants.worldsize
    #     self.corners_not_yet_targeted.append(bottom_left_corner)


    #     top_right_corner = Container()
    #     top_right_corner.x = self.env_constants.worldsize
    #     top_right_corner.y = 0
    #     self.corners_not_yet_targeted.append(top_right_corner)


    #     bottom_right_corner = Container()
    #     bottom_right_corner.x = self.env_constants.worldsize
    #     bottom_right_corner.y = self.env_constants.worldsize
    #     self.corners_not_yet_targeted.append(bottom_right_corner)
    
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
        print "Updated "+str(time_diff)


class PFieldTank(Thread):
    """Handle all command and control logic for a single tank."""
    
    def __init__(self, index, bzrc, corners, env_constants):
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
        self.signal_new_env = Event()
        self.signal_new_env.clear()
        self.signal_done_updating = Event()
        self.signal_done_updating.clear()
        self.command = None
        self.was_just_blind = True
        self.exploration_destination = None
        self.next_explore_point = (0, 0)
        self.past_time_stamp = -1.0
        self.past = []
        self.prev_x = 0
        self.prev_y = 0
        self.obstacle_functions = []
        
        self.goal = Container()
        self.goal.x = -1
        self.goal.y = -1
        self.corners = corners
        self.heading_towards_corner = False
        
    
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
        self.env_state = env_state
        self.signal_done_updating.clear()
        self.signal_new_env.set()
        
        
    
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


    def closest_object_in_a_list(self, tank, obj_list):
        closest_dist = sys.maxint
        chosen_object = obj_list[0]
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
    
    def should_explore(self):
        return self.env_constants.grid.are_there_accessible_unknowns()
    
    def mark_where_ive_been(self, x, y, time_diff):
        if time_diff - self.past_time_stamp > 1.0:
            self.past.append(make_circle_repulsion_function(x, y, 0, 100, 2))
            if len(self.past) > 20:
                self.past.pop(0)
            self.past_time_stamp = time_diff
    
    def get_unstuck(self, x, y, angle, grid):
        if abs(self.prev_x - x) < 0.2 and abs(self.prev_y - y) < 0.2:
            xobs, yobs = self.find_point_in_front()
            self.past = self.past[-2:]
            self.obstacle_functions.append(make_circle_repulsion_function(xobs, yobs, 1, 100, 5))
            #~ self.obstacle_functions.append(make_tangential_function(xobs, yobs, 1, 50, 1, 4))
            if len(self.obstacle_functions) > 20:
                self.obstacle_functions.pop(0)
                #~ self.obstacle_functions.pop(0)
        self.prev_x = x
        self.prev_y = y
    
    def find_point_in_front(self):
        x = self.mytank.x
        y = self.mytank.y
        vx = self.mytank.vx
        vy = self.mytank.vy
        theta = math.atan2(vx, vy)
        dx = self.env_constants.tanklength *math.cos(theta)
        dy = self.env_constants.tanklength *math.sin(theta)
        return x + dx, y + dy
    
    #~ def find_point_in_front(self, x, y, angle, grid):
        #~ dx = 2*self.env_constants.tanklength *math.cos(angle)
        #~ dy = 2*self.env_constants.tanklength *math.sin(angle)
        #~ newx = int(x + dx + self.env_constants.worldsize/2)
        #~ newy = int(y + dy + self.env_constants.worldsize/2)
        #~ if newx < 0:
            #~ newx = 0
        #~ if newy < 0:
            #~ newy = 0
        #~ xmax = 100
        #~ ymax = 100
        #~ if newx + xmax > self.env_constants.worldsize:
            #~ xmax -= newx + xmax - self.env_constants.worldsize
        #~ if newy + ymax > self.env_constants.worldsize:
            #~ ymax -= newy + ymax - self.env_constants.worldsize
        #~ m = grid.obstacle_grid
        #~ for i in xrange(0, xmax):
                #~ for j in xrange(0, ymax):
                    #~ if m[newx + i, newy + j] == grid.OBSTACLE:
                        #~ return (newx + i - self.env_constants.worldsize/2,
                                #~ newy + j - self.env_constants.worldsize/2)
        #~ return (x, y)
        
    def world_to_grid_coord(self, x, y):
        worldsize = self.env_constants.worldsize
        return int(x + worldsize/2), int(y + worldsize/2)
    
    def grid_to_world_coord(self, x, y):
        worldsize = self.env_constants.worldsize
        return x - worldsize/2, y - worldsize/2
    
    def behave(self, env_state):
        """Create a behavior command based on potential fields given an environment state."""
        env_constants = self.env_constants # shorten the name
        bag_o_fields = []
        bag_o_fields.extend(env_constants.get_obstacle_functions())
        self.mytank = env_state.get_mytank(self.index)
        mytank = self.mytank
        worldsize = self.env_constants.worldsize
        
        # should I explore?
        if self.should_explore():
            # check for goal validity
            should_get_new_destination = True
            if self.exploration_destination:
                x, y = self.exploration_destination
                x, y = self.world_to_grid_coord(x, y)
                if self.env_constants.grid.is_unknown(x, y):
                    should_get_new_destination = False
                
            # set a new goal if needed
            self.unknown_points = self.env_constants.grid.get_unknown_pointset(int(mytank.x + worldsize/2), int(mytank.y + worldsize/2), 70)
            if should_get_new_destination:
                if self.unknown_points:
                    i, j = self.unknown_points[random.randint(0, len(self.unknown_points)-1)]
                    self.exploration_destination = self.grid_to_world_coord(i, j)
                else:
                    i, j = self.env_constants.grid.get_random_unknown_point()
                    self.exploration_destination = self.grid_to_world_coord(i, j)
            
            x, y = self.exploration_destination
            bag_o_fields.append(make_circle_attraction_function(x, y, 0, 100, 1.75))
            
            # get sensor update
            if len(self.unknown_points) > 0 or env_state.time_diff - self.last_sensor_poll > 5.0:
                self.last_sensor_poll = env_state.time_diff
                x, y, grid = self.bzrc.get_grid_as_matrix(self.index, env_constants.worldsize)
                env_constants.grid.update(x, y, grid)
        else:
            pass # put other actions unrelated to exploration here
        
        self.mark_where_ive_been(mytank.x, mytank.y, env_state.time_diff)
        bag_o_fields.extend(self.past)
        
        self.get_unstuck(mytank.x, mytank.y, mytank.angle, env_constants.grid)
        bag_o_fields.extend(self.obstacle_functions)
        
        def pfield_function(x, y):
            dx = 0
            dy = 0
            for field_function in bag_o_fields:
                newdx, newdy = field_function(x, y)
                dx += newdx
                dy += newdy
            return dx, dy
        
        dx, dy = pfield_function(mytank.x, mytank.y)


        self.move_to_position(mytank, mytank.x + dx, mytank.y + dy)
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
        self.command = Command(tank.index, 1, 2 * relative_angle, True)
    
    
    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle


# class Corners(object):


#     @classmethod
#     def init_corners_not_yet_targeted(cls, bzrc):
#         cls.corners = []
#         cls.lock = Lock()
#         env_constants = bzrc.get_environment_constants()






class Container(object):
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

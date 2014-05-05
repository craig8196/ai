# Bzrflag
# Copyright 2008-2011 Brigham Young University
#
# This file is part of Bzrflag.
#
# Bzrflag is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Bzrflag is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Bzrflag.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of Bzrflag, please contact the Copyright
# Licensing Office, Brigham Young University, 3760 HBLL, Provo, UT 84602,
# (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

"""Main module for bzrflag game.

Containes main game loop, as well as tank, team, flag etc. classes.

"""
__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import math
import random
import datetime
import logging
import asyncore

import collisiontest
import constants
import config
import graphics
import server

logger = logging.getLogger('game')


class GameLoop:
    """Main control object."""

    def __init__(self, config):
        self.config = config
        if self.config['random_seed'] != -1:
            random.seed(self.config['random_seed'])
        self.game = Game(self, self.config)
        if not self.config['test']:
            self.display = graphics.Display(self, self.config)
        self.running = False
        self.gameover = False
        self.timestamp = datetime.datetime.utcnow()
        self.messages = []

    def start_servers(self):
        """Start servers for each team. """
        for color, team in self.game.teams.items():
            port = self.config[color + '_port']
            address = ('0.0.0.0', port)
            srv = server.Server(address, team, self.game, self.config)
            if not self.config['test']:
                print 'port for %s: %s' % (color, srv.get_port())

    def update_game(self):
        """Updates the game world."""
        now = datetime.datetime.utcnow()
        delta = now - self.timestamp
        self.timestamp = now
        dt = ((24 * 60 * 60) * delta.days
               + delta.seconds
               + (10 ** -6) * delta.microseconds)
        self.game.update(dt)

    def update_graphics(self):
        """Updates graphics based on recent changes to game state.

        Adds and removes sprites from the display, etc.
        """
        while len(self.game.inbox) > 0:
            self.display.add_object(self.game.inbox.pop())
        while len(self.game.trash) > 0:
            self.display.remove_object(self.game.trash.pop())

        # Write any pending messages to the console.
        for message in self.messages:
            self.display.console.write(message)
        self.messages = []

    def loop(self):
        """The main loop of bzrflag.

        Checks events, updates positions, and draws to the screen until
        the pygame window is closed, KeyboardInterrupt, or System Exit.
        """
        self.running = True
        self.start_servers()
        if not self.config['test']:
            self.display.setup()
        try:
            while self.running:
                if self.game.end_game:
                    break
                asyncore.loop(constants.LOOP_TIMEOUT, count=1)
                self.update_game()
                if not self.config['test']:
                    self.update_graphics()
                    self.display.update()
        except KeyboardInterrupt:
            pass
        finally:
            final_scores = '\nFinal Score\n'
            for team in self.game.teams:
                team_total = self.game.teams[team].score.total()
                final_scores += 'Team %s: %d\n' % (team, team_total)
            if not self.config['test']:
                print final_scores

    def kill(self):
        self.running = False
        if not self.config['test']:
            self.display.kill()

    def write_message(self, message):
        self.messages.append(message)


class Game(object):
    """Manages the game data."""

    def __init__(self, game_loop, config):
        self.game_loop = game_loop
        self.config = config
        self.end_game = False

        # queue of objects that need to be created or destroyed
        self.inbox = []
        self.trash = []
        self.timespent = 0.0
        self.timelimit = self.config['time_limit']
        self.inertia_linear = 1
        self.inertia_angular = 1
        self.taunt_timer = 0
        self.taunt_msg = None
        self.taunt_color = None

        # track objects on map
        self.obstacles = [Box(i) for i in self.config.world.boxes]
        self.build_truegrid()
        self.bases = dict((i.color, Base(i)) for i in self.config.world.bases)

        self.teams = {}
        for color,base in self.bases.items():
            self.teams[color] = Team(self, color, base, self.config)

    def update(self, dt):
        """Update the teams."""
        self.timespent += dt
        if self.taunt_msg is not None:
            self.taunt_timer -= dt
            if self.taunt_timer <= 0:
                self.taunt_msg = None
                self.game_loop.display.redraw()
        if self.timespent > self.config['time_limit']:
            self.end_game = True
            return
        for team in self.teams.values():
            team.update(dt)

    def build_truegrid(self):
        """Builds occupancy grid with obstacles in self.obstacles.

        Note: Occupancy grids with rotated obstalces not implemnted.
        """
        self.occgrid = [[0 for i in range(self.config.world.width)] 
                           for j in range(self.config.world.height)]
        offset_x = self.config.world.width/2
        offset_y = self.config.world.height/2
        for o in self.obstacles:
            if o.rot == 0:
                lx = (o.pos[0] - o.size[0]/2, o.pos[1] - o.size[1]/2)
                for x in xrange(o.size[0]):
                    for y in xrange(o.size[1]):
                        self.occgrid[x+lx[0]+offset_x][y+lx[1]+offset_y] = 1
            else:
                # We didn't have enough time to implement occupancy grids with
                # rotated obstalces; we figured it was low priority anyway
                # because it would be really difficult for students to deal
                # with.  If someone implements it sometime, great.  Until then,
                # this is our workaround - the server returns a fail on a
                # request for the occupancy grid if there are rotated
                # obstacles.
                self.occgrid = None
                break

    def obstacle_at(self, x, y):
        """Checks for obstacle at given point."""
        for obstacle in self.obstacles:
            if obstacle.rot == 0:
                return collisiontest.point_in_rect((x, y), obstacle.rect)
            else:
                return collisiontest.point_in_poly((x, y), obstacle.shape)
        return False

    def tanks(self):
        """Iterate through all tanks on the map."""
        for team in self.teams.values():
            for tank in team.tanks:
                yield tank

    def shots(self):
        """Iterate through all shots on the map."""
        for tank in self.tanks():
            for shot in tank.shots:
                yield shot

    def dropFlag(self, flag):
        """Sets flag to None."""
        if flag.tank is not None:
            flag.tank.flag = None
        flag.tank = None

    def returnFlag(self, flag):
        """Return flag to base."""
        if flag.tank is not None:
            flag.tank.flag = None
        flag.tank = None
        flag.pos = flag.team.base.pos

    def scoreFlag(self, flag):
        """Adjust scores for capture."""
        flag.tank.team.score.gotFlag()
        flag.team.score.lostFlag()
        self.returnFlag(flag)

    def closest_base(self, pos):
        """Returns position of clossest base."""
        items = tuple(sorted((collisiontest.get_dist(pos, base.center), base)
                      for base in self.bases.values()))
        if abs(items[0][0] - items[1][0]) < 50:
            return None
        return items[0][1]

    def taunt(self, message, color):
        """Set taunt message for given color."""
        if self.taunt_msg is None:
            self.taunt_msg = message
            self.taunt_timer = 3
            self.taunt_color = color
            return True
        return False

    def write_msg(self, message):
        self.game_loop.display.console.write(message)

class Team(object):
    """Team object:

    Manages a BZRFlag team -- w/ a base, a flag, a score, and tanks.
    """

    def __init__(self, map, color, base, config):
        self.config = config
        self.color = color
        self.map = map
        ntanks = self.config[self.color+'_tanks']
        if ntanks is None:
            ntanks = self.config['default_tanks']

        self.tanks = [Tank(self, i, self.config) for i in xrange(ntanks)]
        self.tanks_radius = constants.TANKRADIUS * ntanks * 3/2.0
        self.base = base
        base.team = self
        self.flag = Flag(self)

        self.posnoise = self.config[self.color+'_posnoise']
        if self.posnoise is None:
            self.posnoise = self.config['default_posnoise']

        self.angnoise = self.config[self.color+'_angnoise']
        if self.angnoise is None:
            self.angnoise = self.config['default_angnoise']

        self.velnoise = self.config[self.color+'_velnoise']
        if self.velnoise is None:
            self.velnoise = self.config['default_velnoise']

        self.score = Score(self)
        self._obstacles = []
        self.setup()
        for item in self.tanks+[self.base, self.flag, self.score]:
            self.map.inbox.append(item)

    def setup(self):
        """Initialize the cache of obstacles near the base."""
        self._obstacles = []
        for o in self.map.obstacles:
            c = self.base.center
            r = self.tanks_radius + constants.TANKRADIUS
            if collisiontest.circle_to_circle((o.center, o.radius), (c, r)):
                self._obstacles.append(o)

    def respawn(self, tank, first=True):
        """Respawn a dead tank."""

        tank.status = constants.TANKALIVE
        tank.reset_speed()
        if tank.pos != constants.DEADZONE:
            return

        tank.rot = random.uniform(0, 2*math.pi)
        pos = self.spawn_position()
        for i in xrange(constants.RESPAWNTRIES):
            if self.check_position(pos, constants.TANKRADIUS):
                break
            pos = self.spawn_position()
        else:
            raise Exception("No workable spawning spots found for team %s"
                            %self.color)
        tank.pos = pos

    def check_position(self, pos, rad):
        """Check a position to see if it is safe to spawn a tank there."""
        for o in self._obstacles:
            if collisiontest.circle_to_poly((pos,rad), o.shape):
                return False
        for s in self.map.shots():
            shot = (s.pos, constants.SHOTRADIUS)
            if collisiontest.circle_to_circle((pos,rad), shot):
                return False
        for t in self.map.tanks():
            tank = (t.pos, constants.TANKRADIUS)
            if collisiontest.circle_to_circle((pos,rad), tank):
                return False
        off_map_left = pos[0]-rad < -self.config.world.size[0]/2
        off_map_bottom = pos[1]-rad < -self.config.world.size[1]/2
        off_map_right = pos[0]+rad > self.config.world.size[0]/2
        off_map_top = pos[1]+rad > self.config.world.size[1]/2
        if off_map_left or off_map_bottom or off_map_right or off_map_top:
            return False
        return True

    def spawn_position(self):
        """Generate a random spawning position around the base."""
        angle = random.uniform(0, 2*math.pi)
        dist = random.uniform(0,1) * self.tanks_radius
        return [self.base.center[0] + dist*math.cos(angle),
                self.base.center[1] + dist*math.sin(angle)]

    def update(self, dt):
        """Update the tanks and flag."""
        for tank in self.tanks:
            tank.update(dt)
        self.flag.update(dt)
        self.score.update(dt)

    def tank(self, id):
        """Get a tank based on its ID."""
        if 0<=id<len(self.tanks):
            return self.tanks[id]
        raise ValueError("Invalid tank ID: %s"%id)

    def shoot(self, tankid):
        """Tell a tank to shoot."""
        return self.tank(tankid).shoot()

    def speed(self, tankid, value):
        """Set a tank's goal speed."""
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        if not (1 >= value >= -1):
            raise Exception("not a number")
        self.tank(tankid).setspeed(value)

    def angvel(self, tankid, value):
        """Set a tank's goal angular velocity."""
        if value > 1:
            value = 1
        elif value < -1:
            value = -1
        if not (1 >= value >= -1):
            raise Exception("not a number")
        self.tank(tankid).setangvel(value)

    def taunt(self, message):
        return self.map.taunt(message, self.color)


class Tank(object):
    """BZFlag Tank

    Handles the logic for dealing with a tank in the game.

    Attributes:
        rot: angular rotation in radians; always between 0 and 2*pi
    """
    size = (constants.TANKRADIUS*2,) * 2
    radius = constants.TANKRADIUS

    def __init__(self, team, tankid, config):
        self.config = config
        self.team = team
        self.pos = constants.DEADZONE
        self.goal_speed = 0
        self.goal_angvel = 0
        self.speed = 0
        self.angvel = 0
        self.rot = 0
        self.callsign = self.team.color + str(tankid)
        self.status = constants.TANKDEAD
        self.shots = []
        self.reloadtimer = 0
        self.dead_timer = -1
        self.flag = None
        self.spawned = False

    def reset_speed(self):
        """Reset rot, speed and angvel to zero."""
        self.goal_speed = 0
        self.goal_angvel = 0
        self.speed = 0
        self.angvel = 0
        self.rot = 0

    def setspeed(self, speed):
        """Set the goal speed."""
        self.goal_speed = speed

    def setangvel(self, angvel):
        """Set the goal angular velocity."""
        self.goal_angvel = angvel

    def shoot(self):
        """Tell the tank to shoot."""
        if self.reloadtimer > 0 or \
                len(self.shots) >= self.config['max_shots']:
            return False
        shot = Shot(self, self.config)
        self.shots.insert(0, shot)
        self.team.map.inbox.append(shot)
        self.reloadtimer = constants.RELOADTIME
        return True

    def kill(self):
        """Kill tank."""
        self.status = constants.TANKDEAD
        self.pos = constants.DEADZONE
        self.dead_timer = self.config['respawn_time']
        self.team.score.score_tank(self)
        if self.flag:
            self.team.map.dropFlag(self.flag)
            self.flag = None
        for shot in self.shots:
            shot.kill()
        self.shots = []

    def collision_at(self, pos):
        """Return True if collision at given position, and False otherwise."""
        rad = constants.TANKRADIUS
        for obs in self.team.map.obstacles:
            if collisiontest.circle_to_poly(((pos),rad), obs.shape):
                return True
        for tank in self.team.map.tanks():
            if tank is self:
                continue
            if collisiontest.circle_to_circle((tank.pos, rad), (pos, rad)):
                self.collide_tank(tank)
                return True
        at_left_wall = pos[0]-rad < -self.config.world.size[0]/2
        at_bottem_wall = pos[1]-rad < -self.config.world.size[1]/2
        at_right_wall = pos[0]+rad > self.config.world.size[0]/2
        at_top_wall = pos[1]+rad > self.config.world.size[1]/2
        if at_left_wall or at_bottem_wall or at_right_wall or at_top_wall:
            return True
        return False

    def collide_tank(self, tank):
        """Pass - Not yet implimented."""
        pass

    def update(self, dt):
        """Update the tank's position, status, velocities."""
        for shot in self.shots:
            shot.update(dt)

        if self.reloadtimer > 0:
            self.reloadtimer -= dt
        if (self.pos == constants.DEADZONE and
            self.status != constants.TANKDEAD):
            self.team.respawn(self)
        if self.status == constants.TANKDEAD:
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.team.respawn(self, not self.spawned)
                self.spawned = True
            return

        self.update_goals(dt)
        dx,dy = self.velocity()
        if not self.collision_at((self.pos[0]+dx*dt,
                                  self.pos[1]+dy*dt)):
            self.pos[0] += dx*dt
            self.pos[1] += dy*dt
        elif not self.collision_at((self.pos[0], self.pos[1]+dy*dt)):
            self.pos[1] += dy*dt
        elif not self.collision_at((self.pos[0]+dx*dt, self.pos[1])):
            self.pos[0] += dx*dt

    def update_goal(self, num, goal, by):
        """Update given num by given amount until equal to given goal."""
        if num < goal:
            num += by
            if num > goal:
                return goal
            return num
        elif num > goal:
            num -= by
            if num < goal:
                return goal
            return num
        else:
            return num

    def update_goals(self, dt):
        """Update the velocities to match the goals."""
        self.speed = self.update_goal(self.speed, self.goal_speed,
                                      constants.LINEARACCEL * dt)
        self.angvel = self.update_goal(self.angvel, self.goal_angvel,
                                       constants.ANGULARACCEL * dt)
        self.rot += self.angvel * constants.TANKANGVEL * dt
        # Normalize the angle to be between 0 and 2*pi
        self.rot = self.rot % (2 * math.pi)

    def velocity(self):
        """Calculate the tank's linear velocity."""
        return (self.speed * math.cos(self.rot) * constants.TANKSPEED,
            self.speed * math.sin(self.rot) * constants.TANKSPEED)


class Shot(object):
    """Shot object:

    Contains the logic for a shot on the map.
    """

    size = (constants.SHOTRADIUS*2,) * 2

    def __init__(self, tank, config):
        self.config = config
        self.tank = tank
        self.team = tank.team
        self.rot = self.tank.rot
        self.distance = 0
        self.pos = tank.pos[:]
        speed = constants.SHOTSPEED + tank.speed
        self.vel = (speed * math.cos(self.rot), speed * math.sin(self.rot))
        self.status = constants.SHOTALIVE

    def update(self, dt):
        """Move the shot."""
        if (self.status == constants.SHOTDEAD or
            self.pos == constants.DEADZONE):
            return
        self.distance += math.hypot(self.vel[0]*dt, self.vel[1]*dt)

        ## do we need to lerp?
        if self.vel[0]*dt > constants.TANKRADIUS*2:
                p1 = self.pos[:]
                p2 = [self.pos[0]+self.vel[0]*dt, self.pos[1]+self.vel[1]*dt]
                self.check_line(p1,p2)
        else:
            self.pos[0] += self.vel[0]*dt
            self.pos[1] += self.vel[1]*dt
            self.check_collisions()
        if self.distance > constants.SHOTRANGE:
            self.kill()

    def check_collisions(self):
        """Check for collisions."""
        s_rad = constants.SHOTRADIUS
        t_rad = constants.TANKRADIUS
        for obs in self.team.map.obstacles:
            if collisiontest.circle_to_poly(((self.pos),s_rad), obs.shape):
                return self.kill()
        for tank in self.team.map.tanks():
            if self in tank.shots:
                continue
            if collisiontest.circle_to_circle((tank.pos, t_rad),
                                              (self.pos, s_rad)):
                if tank.team == self.team and not self.config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        at_left_wall = self.pos[0]-s_rad < -self.config.world.size[0]/2
        at_bottem_wall = self.pos[1]-s_rad < -self.config.world.size[1]/2
        at_right_wall = self.pos[0]+s_rad > self.config.world.size[0]/2
        at_top_wall = self.pos[1]+s_rad > self.config.world.size[1]/2
        if at_left_wall or at_bottem_wall or at_right_wall or at_top_wall:
            return self.kill()

    def check_line(self, p1, p2):
        """Check for collisions."""
        s_rad = constants.SHOTRADIUS
        t_rad = constants.TANKRADIUS
        for obs in self.team.map.obstacles:
            if collisiontest.line_cross_rect((p1,p2), obs.rect):
                return self.kill()
        for tank in self.team.map.tanks():
            if collisiontest.line_cross_circle((p1,p2), (tank.pos, t_rad + s_rad)):
                if tank.team == self.team and not self.config['friendly_fire']:
                    continue
                tank.kill()
                return self.kill()
        at_left_wall = self.pos[0]-s_rad < -self.config.world.size[0]/2
        at_bottem_wall = self.pos[1]-s_rad < -self.config.world.size[1]/2
        at_right_wall = self.pos[0]+s_rad > self.config.world.size[0]/2
        at_top_wall = self.pos[1]+s_rad > self.config.world.size[1]/2
        if at_left_wall or at_bottem_wall or at_right_wall or at_top_wall:
            return self.kill()

    def kill(self):
        """Remove the shot from the map."""
        self.status = constants.SHOTDEAD
        self.tank.team.map.trash.append(self)
        if self in self.tank.shots:
            self.tank.shots.remove(self)


class Flag(object):
    """Flag object:

    Contains the logic for team flags on a map.
    """

    size = (constants.FLAGRADIUS*2,) * 2

    def __init__(self, team):
        self.team = team
        self.rot = 0
        self.pos = team.base.center
        self.tank = None

    def update(self, dt):
        """Update the flag's position."""
        f_rad = constants.FLAGRADIUS
        t_rad = constants.TANKRADIUS
        x, y = self.pos
        if self.tank is not None:
            self.pos = self.tank.pos
            rect = self.tank.team.base.rect
            if collisiontest.circle_to_rect((self.pos, f_rad), rect):
                self.tank.team.map.scoreFlag(self)
        else:
            for tank in self.team.map.tanks():
                if collisiontest.circle_to_circle((self.pos, f_rad),
                                                  (tank.pos, t_rad)):
                    if tank.team is self.team:
                        self.team.map.returnFlag(self)
                    else:
                        self.tank = tank
                        tank.flag = self
                    return


def rotate_scale(p1, p2, angle, scale = 1.0):
    """Rotate p1 around p2 with an angle of angle."""
    theta = math.atan2(p1[1] - p2[1], p1[0] - p2[0])
    dst = math.hypot(p1[0]-p2[0], p1[1]-p2[1]) * scale
    return (p2[0] + dst*math.cos(theta + angle),
        p2[1] + dst*math.sin(theta + angle))


def convertBoxtoPoly(center, size, rotation = 0):
    """Convert a box to a polygon (list of points)."""
    d = (1,1),(1,-1),(-1,-1),(-1,1)
    x,y = center
    w,h = size
    for dx,dy in d:
        yield x + w/2*dx, y + h/2 * dy


def scale_rotate_poly(points, scale, rotation):
    """Rotate shape."""
    points = list(points)
    center = polygon_center(points)
    for point in points:
        yield rotate_scale(point, center, rotation, scale)


def polygon_center(points):
    """Return position of center of polygon."""
    points = tuple(points)
    cx = sum(p[0] for p in points)/len(points)
    cy = sum(p[1] for p in points)/len(points)
    return cx,cy


class Base(object):
    """Base object:

    Contains the logic & data for a team's Base on a map.
    """

    def __init__(self, item):
        self.color = item.color
        self.center = self.pos = item.pos.asList()
        self.size = tuple(x*2 for x in item.size.asList())
        self.radius = math.sqrt((self.size[0]/2)**2 + (self.size[1]/2)**2)
        poly = tuple(convertBoxtoPoly(item.pos,self.size))
        self.rect = (item.pos[0]-self.size[0]/2,
                     item.pos[1]-self.size[1]/2) + self.size
        self.shape = list(scale_rotate_poly(poly, 1, item.rot))
        self.rot = item.rot


class Obstacle(object):
    """Obstacle object:

    Contains the logic and data for an obstacle on the map.
    """

    def __init__(self, item):
        self.center = self.pos = item.pos.asList()
        self.shape = ()
        self.rot = item.rot
        self.radius = 0

    def pad(self, padding):
        """Set shape"""
        self.shape = list(scale_rotate_poly(self.shape,
                         (self.radius + padding)/float(self.radius), 0))


class Box(Obstacle):
    """A Box Obstacle."""

    def __init__(self, item):
        Obstacle.__init__(self, item)
        self.radius = math.hypot(*item.size)
        self.size = tuple(x*2 for x in item.size.asList())
        self.shape = list(scale_rotate_poly((convertBoxtoPoly
                         (item.pos, self.size,item.rot)), 1, item.rot))
        self.rect = (tuple(self.pos)+self.size)


class Score(object):
    """Score object: keeps track of a team's score."""

    def __init__(self, team):
        self.team = team
        self.value = 0
        self.flags = 0
        self.timer = 0

    def update(self, dt):
        """Update scores."""
        self.timer += dt
        if self.timer > 2:
            self.timer = 0
            for tank in self.team.tanks:
                self.score_tank(tank)

    def score_tank(self, tank):
        """Score tank."""
        my_base = self.team.base.center
        if tank.flag:
            ebase = tank.flag.team.base
            dist_to = collisiontest.get_dist(my_base, tank.flag.team.base.center)
            dist_back = collisiontest.get_dist(tank.pos, my_base)
            more = 100.0 * (dist_to - dist_back)/dist_to
            if dist_back > dist_to:
                more = 0
            self.setValue(500 + more)
        else:
            closest = None
            for color,team in self.team.map.teams.items():
                if team is self.team:
                    continue
                dst = collisiontest.get_dist(tank.pos, team.base.center)
                if closest is None or dst < closest[0]:
                    closest = dst, team.base
            if not closest:
                logger.warning("no closest found... %s" % self.team.color)
                return False
            total_dist = collisiontest.get_dist(my_base, closest[1].center)
            dist_to = collisiontest.get_dist(tank.pos, closest[1].center)
            if dist_to > total_dist:
                return
            self.setValue(100.0 * (total_dist-dist_to)/total_dist)

    def gotFlag(self):
        """Udates flag status."""
        self.value = 0
        self.flags += 1

    def lostFlag(self):
        """Udates flag status."""
        self.flags -= 1

    def setValue(self,value):
        """Sets self.value to given value."""
        if value>self.value:
            self.value = value

    def text(self):
        """Print scores."""
        return "Team %s: %d"%(self.team.color, self.total())

    def total(self):
        """Calulates total points."""
        return 1000*self.flags + self.value




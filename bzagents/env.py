from grid import Grid

class EnvironmentState(object):
    """Tracks the state of an environment and provides convenience 
    functions that answer common questions about the state.
    """
    def __init__(self):
        # Fields: color, poss_color, x, y
        self.myflag = None
        self.enemyflags = None
        # Fields: x, y, vx, vy
        self.shots = None
        # Fields: index, callsign, status, shots_avail, time_to_reload, 
        # flag, x, y, angle, vx, vy, angvel
        self.mytanks = None
        # Fields: callsign, color, status, flag, x, y, angle
        self.enemytanks = None
        # Represents the number of seconds since the game started
        self.time_diff = None
    
    def get_mytank(self, index):
        for t in self.mytanks:
            if t.index == index:
                return t

class EnvironmentConstants(object):
    """Tracks the things that don't change in the environment."""
    def __init__(self):
        # Lists of (x, y) tuples defining an obstacle
        self.obstacles = None
        # Fields: color, list (a list of (x, y) tuples)
        self.bases = None
        # Fields: color, count, base (a list of (x, y) tuples)
        self.teams = None
        # Dict Entries: 
        # {'shotspeed': '100', 'tankalive': 'alive', 'truepositive': '1', 
        # 'worldsize': '800', 'explodetime': '5', 'truenegative': '1', 
        # 'shotrange': '350', 'flagradius': '2.5', 'tankdead': 'dead', 
        # 'tankspeed': '25', 'shotradius': '0.5', 'tankangvel': '0.785398163397', 
        # 'linearaccel': '0.5', 'team': 'blue', 'tankradius': '4.32', 'angularaccel': '0.5', 
        # 'tankwidth': '2.8', 'tanklength': '6'}
        self.constants = None
        self.obstacle_functions = []
    
    def get_base_location(self, color):
        for t in self.teams:
            if t.color == color:
                x = 0
                y = 0
                for points in t.base:
                    x += points[0]
                    y += points[1]
                if len(t.base) > 0:
                    return x/len(t.base), y/len(t.base)
        return 0, 0
    
    def set_constants(self, constants):
        self.constants = constants
        print constants
        self.worldsize = int(constants['worldsize'])
        self.alive = constants['tankalive']
        self.dead = constants['tankdead']
        self.color = constants['team']
        self.tanklength = int(constants['tanklength'])
        if 'truepositive' in constants:
            self.truepositive = float(constants['truepositive'])
        else:
            self.truepositive = None
        if 'truenegative' in constants:
            self.truenegative = float(constants['truenegative'])
        else:
            self.truenegative = None
        print self.truepositive, self.truenegative
        if (self.truepositive != None and self.truenegative != None) and \
            (self.truepositive != 1.0 and self.truenegative != 1.0):
            self.occgrid_enabled = True
            self.grid = Grid(self.worldsize, self.worldsize)
            self.grid.set_true_positive(self.truepositive)
            self.grid.set_true_negative(self.truenegative)
        else:
            self.occgrid_enabled = False
            self.grid = None
    
    def get_count(self, teamcolor):
        """Return number of tanks on given team."""
        for team in self.teams:
            if team.color == teamcolor:
                return team.count
        return 0
    
    def get_obstacle_functions(self):
        return self.obstacle_functions

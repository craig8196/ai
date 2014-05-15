

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
    
    def set_constants(self, constants):
        self.constants = constants
        self.worldsize = int(constants['worldsize'])
        self.alive = constants['tankalive']
        self.dead = constants['tankdead']
        self.color = constants['team']
        self.tanklength = constants['tanklength']
        if 'truepositive' in constants:
            self.truepositive = float(constants['truepositive'])
        else:
            self.truepositive = None
        if 'truenegative' in constants:
            self.truenegative = float(constants['truenegative'])
        else:
            self.truenegative = None
        if self.truepositive != None and self.truenegative != None:
            self.occgrid_enabled = True
        else:
            self.occgrid_enabled = False
    
    def get_count(self, teamcolor):
        """Return number of tanks on given team."""
        for base in self.bases:
            if base.color == teamcolor:
                return base.count
        return 0

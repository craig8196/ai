from threading import Thread
from Gnuplot import GnuplotProcess
from utilities import ThreadSafeQueue
from numpy import linspace

class PotentialFieldGraph(Thread):
    """Enables asynchronous graphing using a producer-consumer model."""    
    
    def __init__(self, worldsize=800, samples=25):
        """Graphs only square worlds centered about the origin."""
        super(PotentialFieldGraph, self).__init__()
        self.worldsize = worldsize
        self.samples = samples
        self.vec_len = 0.75*self.worldsize/self.samples
        self.gp = GnuplotProcess(persist=False)
        self.gp.write(self.gnuplot_header(-worldsize/2, worldsize/2))
        self.functions = ThreadSafeQueue()
        self.keep_running = True
    
    def stop(self):
        """Stop graphing."""
        self.keep_running = False
    
    def add_function(self, function):
        """Add another function to graph, the function must be of type
        f(x, y). This is the producer.
        """
        self.functions.add(function)
    
    def remove_function(self):
        """Remove a function from the functions array.
        This is the consumer.
        Return a function of the type f(x, y).
        """
        return self.functions.remove()
    
    def run(self):
        """Continuously graph functions."""
        while self.keep_running:
            f = self.remove_function()
            if self.keep_running:
                self.gp.write(self.plot_field(f))
    
    # Helper functions.
    def gpi_point(self, x, y, vec_x, vec_y):
        '''Create the centered gpi data point (4-tuple) for a position and
        vector.  The vectors are expected to be less than 1 in magnitude,
        and larger values will be scaled down.'''
        r = (vec_x ** 2 + vec_y ** 2) ** 0.5
        if r > 1:
            vec_x /= r
            vec_y /= r
        return (x - vec_x * self.vec_len / 2, y - vec_y * self.vec_len / 2,
                vec_x * self.vec_len, vec_y * self.vec_len)
    
    def gnuplot_header(self, minimum, maximum):
        '''Return a string that has all of the gnuplot sets and unsets.'''
        s = ''
        s += 'set xrange [%s: %s]\n' % (minimum, maximum)
        s += 'set yrange [%s: %s]\n' % (minimum, maximum)
        # The key is just clutter.  Get rid of it:
        s += 'unset key\n'
        # Make sure the figure is square since the world is square:
        s += 'set size square\n'
        # Add a pretty title (optional):
        s += "set title 'Potential Fields'\n"
        return s
    
    def draw_line(self, p1, p2):
        '''Return a string to tell Gnuplot to draw a line from point p1 to
        point p2 in the form of a set command.'''
        x1, y1 = p1
        x2, y2 = p2
        return 'set arrow from %s, %s to %s, %s nohead lt 3\n' % (x1, y1, x2, y2)
    
    def draw_dot(self, x, y):
        return ''
    
    def draw_obstacles(self, obstacles):
        '''Return a string which tells Gnuplot to draw all of the obstacles.'''
        s = 'unset arrow\n'

        for obs in obstacles:
            last_point = obs[0]
            for cur_point in obs[1:]:
                s += self.draw_line(last_point, cur_point)
                last_point = cur_point
            s += self.draw_line(last_point, obs[0])
        return s
    
    def plot_field(self, function):
        '''Return a Gnuplot command to plot a field.'''
        s = "plot '-' with vectors head\n"

        separation = self.worldsize / self.samples
        end = self.worldsize / 2 - separation / 2
        start = -end

        points = ((x, y) for x in linspace(start, end, self.samples)
                    for y in linspace(start, end, self.samples))

        for x, y in points:
            f_x, f_y = function(x, y)
            plotvalues = self.gpi_point(x, y, f_x, f_y)
            if plotvalues is not None:
                x1, y1, x2, y2 = plotvalues
                s += '%s %s %s %s\n' % (x1, y1, x2, y2)
        s += 'e\n'
        return s

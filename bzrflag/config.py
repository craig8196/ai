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

"""Configuration class for the Bzrflag game."""

__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import sys
import os
import optparse
import ConfigParser
import logging

import world

class ParseError(Exception): pass
class ArgumentError(Exception): pass

logger = logging.getLogger("config.py")

class Config:
    """Config class:

    Parses command line options and the --config file if given.
    """

    def __init__(self, args=None):
        self.options = self.parse_cli_args(args)
        self.setup_world()

    def get(self, key, default):
        """Return value of given key, or defalt if option[key] = None."""
        if self.options[key] is None:
            return default
        return self.options[key]

    def __getitem__(self, key):
        return self.options[key]

    def setup_world(self):
        """Parse the world file"""
        if not self.options['world']:
            raise ArgumentError('no world defined')
        if not os.path.isfile(self.options['world']):
            raise ArgumentError('world file not found: %s'\
                %self.options['world'])
        text = open(self.options['world']).read()
        size = int(self.options['world_size'])
        results = world.World.parser(size, size).parseString(text)
        if not results:
            raise ParseError('invalid world file: %s'%config['world'])
        self.world = results[0]

    def parse_cli_args(self, args):
        """Parse command line arguments."""
        p = optparse.OptionParser()

        p.add_option('-d','--debug',
            action='store_true',
            dest='debug',
            help='turn on verbose debugging')
        p.add_option('--test',
            action='store_true',
            dest='test',
            help='run in test mode (no GUI)')
        p.add_option('--debug-out',
            dest='debug_out',
            help='output filename for debug messages')
        p.add_option('--window-size',
            dest='window_size',
            default='800x800',
            help='size of the window to use, ex. 800x800')

        ## game behavior
        p.add_option('--world',
            dest='world',
            default='maps/four_ls.bzw',
            help='specify a world.bzw map to use')
        p.add_option('--world-size',
            dest='world_size',
            default='800',
            help='specify the world size (it is always square)')
        p.add_option('--config',
            dest='config',
            help='set the config file')
        p.add_option('--python-console',
            dest='python_console', default=False,
            action='store_true',
            help='use interactive python shell')
        p.add_option('--telnet-console',
            dest='telnet_console', default=False,
            action='store_true',
            help='use interactive telnet shell (and log server response)')
        p.add_option('--no-report-obstacles',
            action='store_true', default=False,
            dest='no_report_obstacles',
            help='report obstacles? (turn off to force use\
                                     of the occupancy grid)')
        p.add_option('--occgrid-width', type='int',
            default=50, help='width of reported occupancy grid')

        ## tank behavior
        p.add_option('--max-shots',
            type='int',
            dest='max_shots',default=20,
            help='set the max shots')
        p.add_option('--inertia-linear',
            dest='inertia_linear',
            type='int',default=1,
            help='set the linear inertia')
        p.add_option('--inertia-angular',
            dest='inertia_angular',
            type='int',default=1,
            help='set the angular inertia')
        p.add_option('--seed',
            type='int',default=-1,
            dest='random_seed',
            help='set the random seed for world initialization')
        p.add_option('--angular-velocity',
            type='float',
            dest='angular_velocity',
            help='set the angular velocity for tanks (float)')
        p.add_option('--rejoin-time',
            type='int',
            dest='rejoin_time',
            help='set the rejoin delay')
        p.add_option('--explode-time',
            type='int',
            dest='explode_time',
            help='[insert help] what does this do?')
        p.add_option('--grab-own-flag',
            action='store_false',
            dest='grab_own_flag',
            help='enables grabbing your own flag')
        p.add_option('--friendly-fire',
            action='store_false',
            default='true',
            dest='friendly_fire',
            help="don't die on friendly fire")
        p.add_option('--respawn-time',
            type='int',default=10,
            dest='respawn_time',
            help='set the respawn time')
        p.add_option('--time-limit',
            type='int',default=300000,
            dest='time_limit',
            help='set the time limit')

        g = optparse.OptionGroup(p, 'Team Defaults')
        p.add_option_group(g)
        g.add_option('--default-tanks',
                dest='default_tanks',type='int',default=10,
                help='specify the default number of tanks')

        ## random sensor noise
        g.add_option('--default-posnoise',
                dest='default_posnoise',type='float',default=0,
                help='specify the default positional noise')
        g.add_option('--default-velnoise',
                dest='default_velnoise',type='float',default=0,
                help='specify the default velocity noise')
        g.add_option('--default-angnoise',
                dest='default_angnoise',type='float',default=0,
                help='specify the default angular noise')

        ## For the occupancy grid, the probabitities of sensor accuracy
        # p(1|1) // true positive
        # p(1|0) // false positive, easily obtainable from true positive;
        #           false positive = 1 - true positive
        # p(0|0) // true negative
        # p(0|1) // false negative = 1 - true negative
        g.add_option('--default-true-positive',
                dest='default_true_positive',type='float',default=1,
                help='the true positive probability: p(1|1)')
        g.add_option('--default-true-negative',
                dest='default_true_negative',type='float',default=1,
                help='the true negative probability: p(0|0)')

        for color in ['red','green','blue','purple']:
            title = '%s Team Options' % color.capitalize()
            g = optparse.OptionGroup(p, title)
            p.add_option_group(g)
            g.add_option('--%s-port'%color,
                dest='%s_port'%color,type='int',default=0,
                help='specify the port for the %s team'%color)
            g.add_option('--%s-tanks'%color,
                dest='%s_tanks'%color,type='int',
                help='specify the number of tanks for the %s team'%color)
            g.add_option('--%s-posnoise'%color,
                dest='%s_posnoise'%color,type='float',
                help='specify the posnoise for the %s team'%color)
            g.add_option('--%s-velnoise'%color,
                dest='%s_velnoise'%color,type='float',
                help='specify the velnoise for the %s team'%color)
            g.add_option('--%s-angnoise'%color,
                dest='%s_angnoise'%color,type='float',
                help='specify the angnoise for the %s team'%color)

            g.add_option('--%s-true-positive' % color,
                    dest='%s_true_positive' % color, type='float',
                    help='the true positive probability for %s' % color)
            g.add_option('--%s-true-negative' % color,
                    dest='%s_true_negative' % color, type='float',
                    help='the true negative probability for %s' % color)

        opts, args = p.parse_args(args)

        if opts.config:
            configfile = ConfigParser.ConfigParser()
            if not len(configfile.read(opts.config)):
                raise Exception('config file not found')
            if not 'global' in configfile.sections():
                raise Exception('Invalid config file. Make sure "[global]"\
                    is at the top')
            config = dict(configfile.items('global'))

            for key in config:
                if not hasattr(opts,key):
                    raise Exception('invalid configuration option: %s'%key)
                if getattr(opts,key) == None:
                    type = p.get_option('--'+key.replace('_','-')).type
                    value = config[key]
                    if type == 'int':
                        value = int(value)
                    setattr(opts,key,value)

        #if args:
            #p.parse_error('No positional arguments are allowed.')
        return vars(opts)

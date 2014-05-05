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

"""Graphics module:

    Handles all the graphics for bzflag game.

"""
__author__ = "BYU AML Lab <kseppi@byu.edu>"
__copyright__ = "Copyright 2008-2011 Brigham Young University"
__license__ = "GNU GPL"

import os
import math
import pygame

import paths
import pygameconsole
import constants
import config
import game


class ImageCache(object):

    def __init__(self):
        self._ground = None
        self._wall = None
        self.suffixes = {'base':'basetop','shot':'bolt',
                         'tank':'tank','flag':'flag'}
        ## curently lazy loading...is that good?
        self._teamcache = {'base':{},'shot':{},'flag':{},'tank':{}}
        self._cache = {}
        self._tcache = {'scale':{},'rot':{}}

    def ground(self):
        """Creates a surface of the ground image.

        The surface is scaled down using the factor in constants.TILESCALE.
        """
        if not self._cache.has_key('ground'):
            ground = self.load_image(paths.GROUND)
            self._ground = self.scaled_image(ground, constants.TILESCALE)
        return self._ground

    def wall(self):
        """Returns a surface for walls.

        The surface is scaled down using the factor in constants.TILESCALE.
        """
        if not self._wall:
            wall = self.load_image(paths.WALL)
            self._wall = self.scaled_image(wall, constants.TILESCALE)
        return self._wall

    def loadteam(self, type, color):
        """Load team images."""
        if not self._teamcache.has_key(type):
            raise KeyError("invalid image type: %s"%type)
        if not color in constants.COLORNAME:
            raise KeyError("invalid color: %s"%color)
        if not self._teamcache[type].has_key(color):
            self._teamcache[type][color] = \
                    self.load_image('%s_%s.png'%(color, self.suffixes[type]))
        return self._teamcache[type][color]

    def scaled_size(self, size, scale):
        """Scales a size (width-height pair).

        If the scale is None, scaled_size returns the original size unmodified.
        """
        if scale is not None:
            w, h = size
            w = int(round(w * scale))
            h = int(round(h * scale))
            size = w, h
        return size

    def load_image(self, filename):
        """Loads the image with the given filename from the DATA_DIR."""
        path = os.path.join(paths.DATA_DIR, filename)
        image = pygame.image.load(path).convert_alpha()
        return image

    def scaled_image(self, image, scale):
        """Returns scaled image."""
        size = self.scaled_size(image.get_size(), scale)
        return pygame.transform.smoothscale(image, size)

    def _scaled_image(self, image, scale):
        """Scales the given image to the given size."""
        raise Exception('override this method')

    def rotated_image(self, image, rot):
        """Rotate image."""
        nimg = pygame.transform.rotate(image, rot/math.pi*180)
        return nimg

    def tile(self, tile, size):
        """Creates a surface of the given size tiled with the given surface."""
        tile_width, tile_height = tile.get_size()
        width, height = size
        surface = pygame.surface.Surface(size, pygame.SRCALPHA)
        for i in xrange(width // tile_width + 1):
            for j in xrange(height // tile_height + 1):
                surface.blit(tile, (i * tile_width, j * tile_height))
        return surface


class TextSprite(pygame.sprite.Sprite):

    def __init__(self, bzobject, display):
        pygame.sprite.Sprite.__init__(self)
        self.bzobject = bzobject
        self.display = display
        self.rect = pygame.Rect((0,0), (0,0))
        self.maxwidth = 0
        self.refresh()

    def refresh(self):
        """Updates text."""
        self.text = self.bzobject.text()
        lines = self.text.split('\n')
        font = pygame.font.Font(paths.FONT_FILE, constants.FONTSIZE)
        mw = 0
        mh = 0
        for line in lines:
            w,h = font.size(line)
            if w>mw:mw=w
            mh += h
        if mw > self.maxwidth:
            self.maxwidth = mw
        image = pygame.Surface((self.maxwidth,mh))
        at = 0
        for line in lines:
            image.blit(font.render(line, True, (255, 255, 255)), (0,at))
        self.image = image
        image.set_colorkey((0,0,0))
        self.rect.size = image.get_rect().size

    def reposition(self):
        self.rect.center = (0,0)

    def update(self):
        if self.text != self.bzobject.text():
            self.refresh()
        self.reposition()


class Scores:

    def __init__(self):
        self.scores = []

    def add(self,what):
        self.scores.append(what)

    def draw(self, screen):
        y = screen.get_rect().height-10
        w = 0
        for score in self.scores:
            score.update()
            y -= score.rect.height
            if score.rect.width>w:
                w = score.rect.width
        fy = y
        y = screen.get_rect().height-10
        pygame.draw.rect(screen, (0,0,0), (10, fy, w, y-fy))
        tosort = list(sorted((score.bzobject.total(),score)
                      for score in self.scores))

        for num,score in tosort:
            y -= score.rect.height
            screen.blit(score.image, (10,y))


class BZSprite(pygame.sprite.Sprite):
    """Determines how a single object in the game will be drawn.

    The sprite manager uses the sprite's `image` and `rect` attributes to draw
    it.
    """

    def __init__(self, bzobject, image, display, otype=None):
        super(BZSprite, self).__init__()

        self.bzobject = bzobject
        self.display = display
        self.orig_image = image
        self.type = otype
        self.rect = image.get_rect()
        self.prev_rot = None
        self.prev_scale = None
        self._render_image()
        self.update(True)

    def object_size(self):
        """Finds the screen size of the original unrotated bzobject."""
        return self.display.size_world_to_screen(self.bzobject.size)

    def _translate(self):
        """Translates the image to the bzobject's position."""
        self.rect.center = self.display.pos_world_to_screen(self.bzobject.pos)

    def _render_image(self, force=False):
        if not force and self.display.scale == self.prev_scale \
                     and self.bzobject.rot == self.prev_rot:
            return

        image = self._rotate_image(self.orig_image,
                                   self.bzobject.rot * 180/math.pi)
        if self.type == 'shot':
            comp = 3
        elif self.type == 'flag':
            comp = 4
        else:
            comp = 1

        wscale = self.display.world_to_screen_scale()
        isize = image.get_rect().size
        obj_size = wscale[0]*self.bzobject.size[0],\
                   wscale[1]*self.bzobject.size[1]
        orig_size = self.orig_image.get_rect().size
        thescale = [obj_size[0]/orig_size[0] *comp,
                    obj_size[1]/orig_size[1]*comp]
        image = self._rescale_image(image,thescale)

        self.prev_scale = self.display.scale
        self.prev_rot = self.bzobject.rot
        self.image = image

    def _scale_image(self, image, scale):
        size = image.get_rect().size
        nsize = self.display.images.scaled_size(size, scale)
        return pygame.transform.smoothscale(image,nsize)

    def _rescale_image(self, image, scale):
        size = image.get_rect().size
        return pygame.transform.smoothscale(image,(int(size[0]*scale[0]),
                                            int(size[1]*scale[1])))

    def _rotate_image(self, image, rotation):
        return pygame.transform.rotate(image, rotation)

    def update(self, force=False):
        """Overrideable function for creating the image.

        If force is specified, the image should be redrawn even if the
        bzobject doesn't appear to have changed.

        """
        rot = self.bzobject.rot
        self._render_image(force)
        self.rect = self.image.get_rect()
        self._translate()


class TiledBZSprite(BZSprite):
    """A BZSprite with a tiled image."""

    def _render_image(self, force=False):
        self.prev_rot = self.bzobject.rot
        image = self.orig_image
        w,h = self.bzobject.size
        size = self.display.size_world_to_screen((w/2, h/2))
        image = self.display.images.tile(image, size)
        image = self.display.images.rotated_image(image, self.bzobject.rot)
        self.image = image
        self._translate()


class Taunt(object):
    def __init__(self, map):
        self.map = map
        self.text = None
        self.img = None
        self.update()

    def update(self):
        if self.text != self.map.taunt_msg:
            self.text = self.map.taunt_msg
            self.refresh()

    def refresh(self):
        font = pygame.font.Font(paths.FONT_FILE, 32)
        colors = {'red':(255,0,0),'green':(0,255,0),
                  'blue':(0,0,255),'purple':(255,0,255)}
        text = font.render(self.text, True, colors[self.map.taunt_color])
        bg = font.render(self.text, True, (255,255,255))
        self.img = font.render(self.text, True, (0,0,0))
        self.img.blit(bg, (1,1))
        self.img.blit(text, (0,0))

    def draw(self, screen):
        if self.img and self.text:
            w, h = screen.get_rect().size
            mw, mh = self.img.get_rect().size
            screen.blit(self.img, (w/2-mw/2, h/2-mh/2))


class Display(object):
    """Manages all graphics."""
    _imagecache = ImageCache
    _textclass = TextSprite
    _spriteclass = BZSprite
    _taunt = Taunt

    def __init__(self, game_loop, config):
        self.config = config
        self.game_loop = game_loop
        self.world = self.config.world
        self.scores = Scores()
        self.taunt = self._taunt(self.game_loop.game)
        self.screen_size = map(int, self.config['window_size'].split('x'))
        self.images = self._imagecache()
        self._background = None
        self.spritemap = {}
        self.scale = 1
        self.pos = [0,0]

    def setup(self):
        """Initializes pygame and creates the screen surface."""
        pygame.init()
        pygame.key.set_repeat(200,50)
        self.setup_screen()
        self.sprites = pygame.sprite.LayeredUpdates()
        if self.config['python_console']:
            cons = pygameconsole.PyConsole
        else:
            cons = pygameconsole.TelnetConsole
        self.console = cons(self.game_loop, (25,self.screen_size[1]*2/3-25,
                            self.screen_size[0]-50,self.screen_size[1]/3))

    def setup_screen(self):
        """Sets up screen display."""
        size = self.screen_size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self._screen = pygame.Surface(self.screen_size)
        self._background = None
        bg = self.background()
        self.screen.blit(bg, (0, 0))
        pygame.display.update()

    def resize(self, w, h):
        """Resize the pygame surface."""
        self.screen_size = w, h
        self.setup_screen()
        for sprite in self.sprites:
            sprite.update(True)
        self.redraw()

    def rescale(self, scale, pos):
        """Rescales display."""
        if scale < 1:
            return False
        if scale > 20:
            return False
        oscale = self.scale
        self.scale = scale

        realpos = (pos[0] - self.pos[0])/oscale, (pos[1] - self.pos[1])/oscale
        self.pos[0] = pos[0] - realpos[0]*self.scale
        self.pos[1] = pos[1] - realpos[1]*self.scale

    def redraw(self):
        """Redraws display."""
        size = self._normal_background.get_rect().size
        if self.pos[0]>0:self.pos[0] = 0
        if self.pos[1]>0:self.pos[1] = 0
        if self.pos[0]<self.screen_size[0] - size[0]*self.scale:
            self.pos[0] = self.screen_size[0] - size[0]*self.scale
        if self.pos[1]<self.screen_size[1] - size[1]*self.scale:
            self.pos[1] = self.screen_size[1] - size[1]*self.scale
        ## problem: jerky background.
        tmp = pygame.Surface((size[0]/self.scale,size[1]/self.scale))
        tmp.blit(self._normal_background, (self.pos[0]/self.scale-1,
                                           self.pos[1]/self.scale-1))
        self._background = pygame.transform.smoothscale(tmp, size)
        self.screen.blit(self._background,(0,0))
        self.sprites.update()
        for layer in self.sprites.layers():
            for sprite in self.sprites.get_sprites_from_layer(layer):
                self.screen.blit(sprite.image,sprite.rect)
        self.console.draw(self.screen)

    def background(self):
        """Creates a surface of the background with all obstacles.

        Obstacles includes both bases and boxes.
        """
        if not self._background:
            wscale = self.world_to_screen_scale()
            bg = self.images.tile(self.images.ground(), self.screen_size)
            for box in self.game_loop.game.obstacles:
                s = TiledBZSprite(box, self.images.wall(), self)
                bg.blit(s.image, s.rect.topleft)
            self._normal_background = self._background = bg
        return self._background

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        bg = self.background()
        self.sprites.clear(self.screen, bg)
        self.sprites.update()
        changes = self.sprites.draw(self.screen)
        ## add a check for pygame input later
        self.process_events()
        self.scores.draw(self.screen)
        self.console.draw(self.screen)
        self.taunt.update()
        self.taunt.draw(self.screen)
        pygame.display.flip()

    def process_events(self):
        dirty = False
        for e in pygame.event.get():
            self.console.event(e)
            if e.type == pygame.QUIT:
                self.game_loop.running = False
                self.game_loop.game.end_game = True
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4:
                    dirty = True
                    self.rescale(self.scale*1.1, e.pos)
                elif e.button == 5:
                    self.rescale(self.scale*(1/1.1), e.pos)
                    dirty = True
            elif e.type == pygame.KEYDOWN:
                amt = 20
                if not self.console.minimized:
                    continue
                if e.key == pygame.K_DOWN:
                    self.pos[1] -= amt
                elif e.key == pygame.K_UP:
                    self.pos[1] += amt
                elif e.key == pygame.K_LEFT:
                    self.pos[0] += amt
                elif e.key == pygame.K_RIGHT:
                    self.pos[0] -= amt
                else:
                    continue
                dirty = True
            elif e.type == pygame.MOUSEMOTION:
                if e.buttons[0]:
                    self.pos[0]+=e.rel[0]
                    self.pos[1]+=e.rel[1]
                    dirty = True
            elif e.type == pygame.VIDEORESIZE:
                w,h = e.size
                x = min(w, h)
                self.resize(x, x)
        if dirty:
            self.redraw()

    def pos_world_to_screen(self, pos):
        """Converts a position from world space to screen pixel space.

        >>> pos_world_to_screen((0, 0), (800, 800), (400, 400))
        (200, 200)
        >>> pos_world_to_screen((-400, -400), (800, 800), (400, 400))
        (0, 400)
        >>>
        """
        x, y = pos
        world_width, world_height = self.world.size
        x += world_width / 2
        y -= world_height / 2
        x, y = self.vec_world_to_screen((x, y))
        return x+self.pos[0], y+self.pos[1]

    def size_world_to_screen(self, size):
        """Converts sizes from BZFlag world space to screen space.

        Note that bzflag sizes are more like a radius (half of width), so we
        double them to normalize.
        """
        w, h = size
        w *= 2
        h *= -2
        screen_size = self.vec_world_to_screen((w, h))
        return screen_size

    def vec_world_to_screen(self, vector):
        """Converts a vector from world space to screen pixel space.

        >>> vec_world_to_screen((200, 200), (800, 800), (400, 400))
        (100, -100)
        >>>
        """
        wscale,hscale = self.world_to_screen_scale()
        x, y = vector
        return int(round(x * wscale)), -int(round(y * hscale))

    def world_to_screen_scale(self):
        screen_width, screen_height = self.screen_size
        world_width, world_height = self.world.size
        wscale = screen_width / float(world_width) * self.scale
        hscale = screen_height / float(world_height) * self.scale
        return wscale, hscale

    def add_object(self, obj):
        """Addes given object to display."""
        types = (game.Tank, 'tank'), (game.Shot,'shot'), (game.Flag,'flag'), \
                (game.Base,'base'), (game.Score,'score')
        otype = None
        for cls,name in types:
            if isinstance(obj,cls):
                otype = name
                break
        else:
            raise Exception('invalid object added to display: %s'%obj)
        if otype == 'score':
            sprite = self._textclass(obj, self)
            self.scores.add(sprite)
        else:
            image = self.images.loadteam(otype, obj.team.color)
            sprite = self._spriteclass(obj, image, self, otype)
            self.add_sprite(sprite, otype)
            self.spritemap[obj] = sprite

    def remove_object(self, obj):
        self.remove_sprite(self.spritemap[obj])

    def add_sprite(self,sprite,otype):
        self.sprites.add(sprite,layer = ['base','tank',
                                         'flag','shot','score'].index(otype))

    def remove_sprite(self, sprite):
        self.sprites.remove(sprite)

    def kill(self):
        pygame.display.quit()

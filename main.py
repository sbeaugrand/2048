__version__ = '1.4.0'

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, OptionProperty, ObjectProperty
from kivy.graphics import Color, BorderImage
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.core.window import Window, Keyboard
from kivy.utils import platform
from kivy.factory import Factory
from random import choice, random
from achievement import Achievement

app = None
achievement = None


class ButtonBehavior(object):
    # XXX this is a port of the Kivy 1.8.0 version, the current android versino
    # still use 1.7.2. This is going to be removed soon.
    state = OptionProperty('normal', options=('normal', 'down'))
    last_touch = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        super(ButtonBehavior, self).__init__(**kwargs)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if super(ButtonBehavior, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self.last_touch = touch
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        if super(ButtonBehavior, self).on_touch_move(touch):
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ButtonBehavior, self).on_touch_up(touch)
        assert (self in touch.ud)
        touch.ungrab(self)
        self.last_touch = touch
        self._do_release()
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass


class Number(Widget):
    number = NumericProperty(2)
    scale = NumericProperty(.1)
    colors = {
        2: get_color_from_hex('#eee4da'),
        4: get_color_from_hex('#ede0c8'),
        8: get_color_from_hex('#f2b179'),
        16: get_color_from_hex('#f59563'),
        32: get_color_from_hex('#f67c5f'),
        64: get_color_from_hex('#f65e3b'),
        128: get_color_from_hex('#edcf72'),
        256: get_color_from_hex('#edcc61'),
        512: get_color_from_hex('#edc850'),
        1024: get_color_from_hex('#edc53f'),
        2048: get_color_from_hex('#edc22e'),
        4096: get_color_from_hex('#ed702e'),
        8192: get_color_from_hex('#ed4c2e')
    }

    def __init__(self, **kwargs):
        super(Number, self).__init__(**kwargs)
        anim = Animation(scale=1., d=.15, t='out_quad')
        anim.bind(on_complete=self.clean_canvas)
        anim.start(self)

    def clean_canvas(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()

    def move_to_and_destroy(self, pos):
        self.destroy()
        anim = Animation(opacity=0., d=.25, t='out_quad')
        anim.bind(on_complete=self.destroy)
        anim.start(self)

    def destroy(self, *args):
        if self.parent:
            self.parent.remove_widget(self)

    def move_to(self, pos):
        if self.pos == pos:
            return
        Animation(pos=pos, d=.1, t='out_quad').start(self)

    def on_number(self, instance, value):
        achievement.register(app, value)


class Game2048(Widget):

    cube_size = NumericProperty(10)
    cube_padding = NumericProperty(10)
    score = NumericProperty(0)
    dim = 4

    def __init__(self, **kwargs):
        super(Game2048, self).__init__()
        self.grid = [[None for x in range(self.dim)] for x in range(self.dim)]

        # bind keyboard
        Window.bind(on_key_down=self.on_key_down)
        Window.on_keyboard = lambda *x: None

    def on_key_down(self, window, key, *args):
        moved = False
        if key == 273:
            moved = self.move_topdown(True, from_keyboard=True)
        elif key == 274:
            moved = self.move_topdown(False, from_keyboard=True)
        elif key == 276:
            moved = self.move_leftright(False, from_keyboard=True)
        elif key == 275:
            moved = self.move_leftright(True, from_keyboard=True)
        elif key == Keyboard.keycodes['r']:
            self.restart()
            return
        elif key == Keyboard.keycodes['4']:
            if app.dim != 4:
                app.resize(4)
                return
        elif key == Keyboard.keycodes['5']:
            if app.dim != 5:
                app.resize(5)
                return
        elif key == Keyboard.keycodes['u']:
            self.undo()
            return
        elif key == 27 and platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.mActivity.moveTaskToBack(True)
            return True
        if not self.check_end() and moved:
            Clock.schedule_once(self.spawn_number, .20)

    def rebuild_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0xbb / 255., 0xad / 255., 0xa0 / 255.)
            BorderImage(pos=self.pos, size=self.size, source='data/round.png')
            Color(0xcc / 255., 0xc0 / 255., 0xb3 / 255.)
            csize = self.cube_size, self.cube_size
            for ix, iy in self.iterate_pos():
                BorderImage(pos=self.index_to_pos(ix, iy),
                            size=csize,
                            source='data/round.png')

    def reposition(self, *args):
        l = min(self.width, self.height)
        self.cube_padding = (1.0 * l / self.dim) / (2 * self.dim)
        self.cube_size = 1.0 * (l - (self.cube_padding *
                                     (self.dim + 1))) / self.dim

        self.rebuild_background()

        for ix, iy, number in self.iterate():
            number.size = self.cube_size, self.cube_size
            number.pos = self.index_to_pos(ix, iy)

    def iterate(self):
        for ix, iy in self.iterate_pos():
            child = self.grid[ix][iy]
            if child:
                yield ix, iy, child

    def iterate_empty(self):
        for ix, iy in self.iterate_pos():
            child = self.grid[ix][iy]
            if not child:
                yield ix, iy

    def iterate_pos(self):
        for ix in range(self.dim):
            for iy in range(self.dim):
                yield ix, iy

    def index_to_pos(self, ix, iy):
        padding = self.cube_padding
        cube_size = self.cube_size
        return [(self.x + padding) + ix * (cube_size + padding),
                (self.y + padding) + iy * (cube_size + padding)]

    def spawn_number(self, *args):
        empty = list(self.iterate_empty())
        if not empty:
            return
        value = choice([2] * 9 + [4])
        ix, iy = choice(empty)
        self.spawn_number_at(ix, iy, value)

    def spawn_number_at(self, ix, iy, value):
        number = Number(size=(self.cube_size, self.cube_size),
                        pos=self.index_to_pos(ix, iy),
                        number=value)
        self.grid[ix][iy] = number
        self.add_widget(number)

    def on_touch_up(self, touch):
        v = Vector(touch.pos) - Vector(touch.opos)
        if v.length() < dp(20):
            return

        # detect direction
        dx, dy = v
        if abs(dx) > abs(dy):
            self.move_leftright(dx > 0)
        else:
            self.move_topdown(dy > 0)
        return True

    def move_leftright(self, right, from_keyboard=False):
        last_num = self.get_num()
        last_score = self.score
        r = range(self.dim - 1, -1, -1) if right else range(self.dim)
        grid = self.grid
        moved = False

        for iy in range(self.dim):  # get all the cube for the current line
            cubes = []
            for ix in r:
                cube = grid[ix][iy]
                if cube:
                    cubes.append(cube)

            # combine them
            self.combine(cubes)

            # update the grid
            for ix in r:
                cube = cubes.pop(0) if cubes else None
                if grid[ix][iy] != cube:
                    moved = True
                grid[ix][iy] = cube
                if not cube:
                    continue
                pos = self.index_to_pos(ix, iy)
                if cube.pos != pos:
                    cube.move_to(pos)

        if moved:
            self.last_num = last_num
            self.last_score = last_score

        if from_keyboard:
            return moved
        elif not self.check_end() and moved:
            Clock.schedule_once(self.spawn_number, .20)

    def move_topdown(self, top, from_keyboard=False):
        last_num = self.get_num()
        last_score = self.score
        r = range(self.dim - 1, -1, -1) if top else range(self.dim)
        grid = self.grid
        moved = False

        for ix in range(self.dim):
            # get all the cube for the current line
            cubes = []
            for iy in r:
                cube = grid[ix][iy]
                if cube:
                    cubes.append(cube)

            # combine them
            self.combine(cubes)

            # update the grid
            for iy in r:
                cube = cubes.pop(0) if cubes else None
                if grid[ix][iy] != cube:
                    moved = True
                grid[ix][iy] = cube
                if not cube:
                    continue
                pos = self.index_to_pos(ix, iy)
                if cube.pos != pos:
                    cube.move_to(pos)

        if moved:
            self.last_num = last_num
            self.last_score = last_score

        if from_keyboard:
            return moved
        elif not self.check_end() and moved:
            Clock.schedule_once(self.spawn_number, .20)

    def combine(self, cubes):
        if len(cubes) <= 1:
            return cubes
        index = 0
        while index < len(cubes) - 1:
            cube1 = cubes[index]
            cube2 = cubes[index + 1]
            if cube1.number == cube2.number:
                cube1.number *= 2
                self.score += cube1.number
                cube2.move_to_and_destroy(cube1.pos)
                del cubes[index + 1]

            index += 1

    def check_end(self):
        # we still have empty space
        if any(self.iterate_empty()):
            return False

        # check if 2 numbers of the same type are near each others
        if self.have_available_moves():
            return False

        self.end()
        return True

    def have_available_moves(self):
        grid = self.grid
        for iy in range(self.dim):
            for ix in range(self.dim - 1):
                cube1 = grid[ix][iy]
                cube2 = grid[ix + 1][iy]
                if cube1.number == cube2.number:
                    return True

        for ix in range(self.dim):
            for iy in range(self.dim - 1):
                cube1 = grid[ix][iy]
                cube2 = grid[ix][iy + 1]
                if cube1.number == cube2.number:
                    return True

    def end(self):
        global achievement
        end = self.ids.end.__self__
        self.remove_widget(end)
        self.add_widget(end)
        text = 'Game\nover!'
        for ix, iy, cube in self.iterate():
            if cube.number >= 2048:
                text = 'WIN !'
                break
        self.ids.end_label.text = text
        Animation(opacity=1., d=.5).start(end)
        achievement.gs_score(self.score)
        self.last_num = None

    def restart(self):
        self.score = 0
        self.resize(self.dim)
        Clock.schedule_once(self.spawn_number, .1)
        Clock.schedule_once(self.spawn_number, .1)

    def resize(self, d):
        for ix, iy, child in self.iterate():
            child.destroy()
        self.dim = d
        self.grid = [[None for x in range(self.dim)] for x in range(self.dim)]
        self.reposition()
        self.ids.end.opacity = 0
        self.last_num = None

    def undo(self):
        if self.last_num:
            for ix, iy, child in self.iterate():
                child.destroy()
            self.grid = [[None for x in range(self.dim)]
                         for x in range(self.dim)]
            self.reposition()
            num = [int(x) for x in self.last_num.split(',')]
            self.set_num(num, self.last_score)

    def get_num(self):
        num = ''
        for ix, iy in self.iterate_pos():
            if num != '':
                num += ','
            child = self.grid[ix][iy]
            if child:
                num += str(child.number)
            else:
                num += '0'
        return num

    def set_num(self, num, score):
        i = 0
        n = 0
        for ix, iy in self.iterate_pos():
            value = num[i]
            if value > 0:
                self.spawn_number_at(ix, iy, value)
                n += 1
            i += 1
        self.score = score
        return n


class Game2048App(App):
    use_kivy_settings = False

    def build_config(self, config):
        config.setdefaults('section1', {'dim': '4'})
        config.setdefaults('section4', {'num': '0,' * 15 + '0', 'score': 0})
        config.setdefaults('section5', {'num': '0,' * 24 + '0', 'score': 0})
        self.read_config()

    def read_config(self):
        self.config.read(self.get_running_app().get_application_config())
        self.dim = int(self.config.get('section1', 'dim'))
        self.num4 = self.config.get('section4', 'num')
        self.num5 = self.config.get('section5', 'num')
        self.score4 = int(self.config.get('section4', 'score'))
        self.score5 = int(self.config.get('section5', 'score'))

    def write_config(self):
        if self.dim == 4:
            self.num4 = self.root.ids.game.get_num()
            self.score4 = self.root.ids.game.score
        if self.dim == 5:
            self.num5 = self.root.ids.game.get_num()
            self.score5 = self.root.ids.game.score
        self.config.set('section1', 'dim', self.dim)
        self.config.set('section4', 'num', self.num4)
        self.config.set('section5', 'num', self.num5)
        self.config.set('section4', 'score', self.score4)
        self.config.set('section5', 'score', self.score5)
        self.config.write()

    def build(self):
        global app, achievement
        app = self
        achievement = Achievement(self)
        achievement.set_config(app.config)
        achievement.setup_ui()
        self.resize(self.dim)

    def resize(self, d):
        if self.dim != d:
            self.write_config()
        self.dim = d
        self.root.ids.game.resize(d)
        if self.dim == 4:
            num = [int(x) for x in self.num4.split(',')]
            score = self.score4
        if self.dim == 5:
            num = [int(x) for x in self.num5.split(',')]
            score = self.score5
        if self.root.ids.game.set_num(num, score) == 0:
            self.root.ids.game.restart()

    def on_pause(self):
        achievement.on_pause()
        self.write_config()
        return True

    def on_stop(self):
        self.write_config()

    def on_resume(self):
        achievement.on_resume()

    def _on_keyboard_settings(self, *args):
        return


if __name__ == '__main__':
    Factory.register('ButtonBehavior', cls=ButtonBehavior)
    Game2048App().run()

import numpy as np
import random
import pickle

import painterwidget

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty
from kivy.graphics import Color, Ellipse, Rectangle, Line

from kivy.animation import Animation
from kivy.utils import get_color_from_hex, get_hex_from_color

from kivy.core.text import LabelBase
LabelBase.register(name='modak', fn_regular='fonts/Modak-Regular.ttf')

colors = {
    'screen': '#113f67',
    'game_screen': '#e8e8e8',
    'btn': '#38598b',
    'red': '#5e0606',
    'green': '#36622b'
}
colors = {k: get_color_from_hex(v) for k, v in colors.items()}


class MainMenu(Screen):
    lbl_highscore = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)

        # getting highscore from the file
        try:
            with open('highscore.dat', 'rb') as f:
                self.highscore = pickle.load(f)
        except:
            self.highscore = 0

        self.lbl_highscore.text = 'Highscore: {:d}'.format(self.highscore)

    def update_highscore(self, new_highscore):
        self.lbl_highscore.text = 'Highscore: {:d}'.format(new_highscore)

        # save highscore to file
        with open('highscore.dat', 'wb') as f:
            pickle.dump(new_highscore, f)

        self.highscore = new_highscore


class HelpScreen(Screen):
    pass


class GameOverScreen(Screen):
    lbl = ObjectProperty(None)

    def set_score(self, score, is_new_highscore):
        self.lbl.text = '[b][size=56sp]Game over![/size][/b]\n[size=24sp]Score: {:d}[/size]'.format(score)

        if is_new_highscore:
            self.lbl.text += '\n[color=#00dd00][size=24sp]New highscore![/size][/color]'


class GameScreen(Screen):
    desired_pic = ObjectProperty(None)
    lbl_timer = ObjectProperty(None)
    painter = ObjectProperty(None)
    l_tools = ObjectProperty(None)
    btn_start = ObjectProperty(None)
    btn_undo = ObjectProperty(None)
    btn_clear = ObjectProperty(None)
    lbl_score = ObjectProperty(None)
    score = NumericProperty(0)

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

        self.timer = None
        self.remaining_time = 0
        self.cur_pic = 0

        with open('pictures.dat', 'rb') as f:
            self.pictures = pickle.load(f)

        self.desired_pic.allow_stretch = True

    def new_game(self):
        self.remaining_time = 30
        self.timer = Clock.schedule_interval(self.update_time, 1./60)

        self.score = 0

        self.cur_pic = 0
        random.shuffle(self.pictures)
        self.desired_pic.source = self.pictures[0]['src']

        self.painter.disabled = False
        self.l_tools.disabled = False
        self.btn_start.text = 'Check'

    def game_end(self):
        scr_main = self.manager.get_screen('main')
        scr_gameover = self.manager.get_screen('gameover')

        is_new_highscore = self.score > scr_main.highscore

        if is_new_highscore:
            scr_main.update_highscore(self.score)

        scr_gameover.set_score(self.score, is_new_highscore)

        if self.timer is not None:
            self.timer.cancel()
        self.lbl_timer.text = ''
        self.painter.clear()
        self.painter.disabled = True
        self.l_tools.disabled = True
        self.btn_start.text = 'Start'
        self.desired_pic.source = ''
        self.score = 0

        self.manager.current = 'gameover'

    def btn_start_clb(self):
        # if the timer is already running
        if self.timer is not None and self.timer.is_triggered:
            self.check()
        else:
            self.new_game()

    def check(self):
        bitmap = self.painter.bitmap().flatten()
        weights = self.pictures[self.cur_pic]['weights'].flatten().reshape(len(bitmap), 1)
        acc_score = bitmap @ weights

        ideal = self.pictures[self.cur_pic]['ideal']

        if acc_score / ideal > 0.5:
            # next picture
            self.remaining_time += 10
            self.cur_pic += 1
            self.score += 1

            # if the last picture
            if self.cur_pic == len(self.pictures):
                random.shuffle(self.pictures)
                self.cur_pic = 0

            self.desired_pic.source = self.pictures[self.cur_pic]['src']

            self.painter.clear()

            self.show_result('good')
        else:
            self.remaining_time -= 2
            self.show_result('bad')

        print('Ideal: {:d}, score: {:d}, percent: {:.2f}'.format(
            ideal,
            acc_score[0],
            acc_score[0] / ideal * 100
        ))

    def show_result(self, type):
        lbl = Label(font_size='64sp', opacity=1, font_name='modak',
            size_hint=(None, None), size=self.painter.size, pos=self.painter.pos)
        self.add_widget(lbl)

        if type == 'good':
            msgs = ('Good work!', 'Perfect!', 'Well done!', 'Not bad!', 'Excellent!', 'Keep it up!')
            lbl.color = colors['green']
            lbl.text = random.choice(msgs)
            self.lbl_timer.color = colors['green']
        elif type == 'bad':
            lbl.color = colors['red']
            lbl.text = 'Try again!'
            self.lbl_timer.color = colors['red']

        self.lbl_timer.bold = True

        def start_anim(dt):
            change_opacity = Animation(opacity=0.1, duration=.3)
            change_opacity.start(lbl)

            def restore(dt):
                self.remove_widget(lbl)
                self.lbl_timer.color = (0, 0, 0, 1)
                self.lbl_timer.bold = False
            Clock.schedule_once(restore, .3)
        Clock.schedule_once(start_anim, .3)

    def update_time(self, dt):
        self.remaining_time -= dt
        if self.remaining_time <= 0:
            self.game_end()
        else:
            self.lbl_timer.text = 'Remaining: {:.2f}'.format(self.remaining_time)

    def on_score(self, instance, value):
        self.lbl_score.text = 'Score: {:d}'.format(value)


class DrawitApp(App):

    def build(self):
        Window.bind(on_keyboard=self.hook_keyboard)

        self.sm = ScreenManager()

        self.sm.add_widget(MainMenu())
        self.sm.add_widget(HelpScreen())
        self.sm.add_widget(GameScreen())
        self.sm.add_widget(GameOverScreen())

        return self.sm

    def hook_keyboard(self, window, key, *largs):
        # disable back button
        if key == 27:
            return True


if __name__ == '__main__':
    DrawitApp().run()

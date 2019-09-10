import numpy as np
import pickle

from kivy.uix.widget import Widget
from kivy.graphics import (Canvas, Color, Line, Rectangle, Ellipse,
                            Translate, Fbo, ClearColor, ClearBuffers, Scale)


class PainterWidget(Widget):

    disabled = True

    def __init__(self, **kwargs):
        super(PainterWidget, self).__init__(**kwargs)

        self.history = []

        self.bind(size=self.update)
        self.bind(pos=self.update)

    def update(self, *args):
        self.canvas.after.clear()
        self.add_cross()

    def clear(self):
        self.canvas.clear()
        self.history.clear()

    def undo(self):
        if len(self.history) > 0:
            # remove line
            self.canvas.remove(self.history.pop())
            # remove ellipse
            self.canvas.remove(self.history.pop())

    def on_touch_down(self, touch):
        if not self.disabled and self.collide_point(*touch.pos):
            with self.canvas:
                Color(0, 0, 0, 1)
                rad = self.width / 18
                self.history.append(Ellipse(pos=(touch.x - rad / 2,
                    touch.y - rad / 2), size=(rad, rad)))
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=rad / 2)
                self.history.append(touch.ud['line'])

    def on_touch_move(self, touch):
        if not self.disabled and self.collide_point(*touch.pos) and 'line' in touch.ud:
            touch.ud['line'].points += [touch.x, touch.y]

    def bitmap(self):
        # self.export_to_png('test.png')

        # remove cross
        self.canvas.after.clear()

        image_scale = 36 / self.width

        fbo = Fbo(size=(36, 27), with_stencilbuffer=True)

        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            Scale(image_scale, -image_scale, image_scale)
            Translate(-self.x, -self.y - self.height, 0)

        fbo.add(self.canvas)
        fbo.draw()
        # fbo.texture.save('test_small.png', flipped=False)
        bm = np.fromstring(fbo.pixels, dtype=np.uint8).reshape(fbo.size[1], fbo.size[0], 4)
        fbo.remove(self.canvas)

        # return cross
        self.add_cross()

        return np.int64(np.all(bm[:, :, :3] == 0, axis=2))

    def add_cross(self):
        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            Line(points=(self.center_x, self.height + self.y, self.center_x, self.y), width=1)
            Line(points=(self.x, self.center_y, self.width, self.center_y), width=1)

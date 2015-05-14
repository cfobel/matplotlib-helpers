# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


class PointsHandler(object):
    def __init__(self, axis, legend=True, poly_color='grey'):
        self.dragged = None

        left, right = axis.get_xlim()
        bottom, top = axis.get_ylim()
        x = np.array([left, left, right, right])
        y = np.array([top, bottom, top, bottom])
        index = ['upper left', 'lower left', 'upper right', 'lower right']
        self.init_points = pd.DataFrame(np.column_stack([x, y]),
                                        columns=['x', 'y'], index=index)
        self.size = pd.Series(.05 * np.array([abs(right - left),
                                              abs(top - bottom)]),
                              index=['x', 'y'])
        self.init_points['dx'] = [0, 0, -self.size.x, -self.size.x]
        self.init_points['dy'] = [0, -self.size.y, 0, -self.size.y]

        colors = axis._get_lines.color_cycle

        self.boxes = pd.Series([Rectangle((r.x + r.dx, r.y + r.dy),
                                          self.size.x, self.size.y, alpha=0.4,
                                          picker=5, facecolor=colors.next(),
                                          edgecolor='black', linewidth=2)
                                for i, r in self.init_points.iterrows()],
                               index=self.init_points.index)

        for b in self.boxes:
            axis.add_patch(b)

        # Connect events and callbacks
        fig = axis.get_figure()
        fig.canvas.mpl_connect("pick_event", self.on_pick_event)
        fig.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        fig.canvas.mpl_connect("button_release_event", self.on_release_event)

        self.axis = axis
        self.handler_index = 0
        self.handlers = {}
        self.poly = None
        self.poly_kwargs = dict(linestyle='--', alpha=0.8, color=poly_color,
                                refresh=True)
        self.draw_poly(**self.poly_kwargs)

        self.connect('box_move_event', lambda *args:
                     self.draw_poly(**self.poly_kwargs))

        if legend:
            self.legend()

    def reset(self):
        old_points = self.points
        points = self.init_points[['x', 'y']].copy()
        points += self.init_points[['dx', 'dy']].values

        for i, b in self.boxes.iteritems():
            old_point = old_points.ix[i]
            new_point = points.ix[i]
            b.set_xy(new_point)
            for signal, callback in self.handlers.itervalues():
                if signal == 'box_move_event':
                    callback(b, old_point, new_point)
                elif signal == 'box_release_event':
                    callback(b, new_point)

    def draw_poly(self, **kwargs):
        refresh = kwargs.pop('refresh', False)
        index = ['upper left', 'lower left', 'lower right', 'upper right',
                 'upper left']

        xlim = self.axis.get_xlim()
        ylim = self.axis.get_ylim()

        poly_points = self.points.ix[index]

        if self.poly is not None:
            self.poly.remove()

        self.poly = self.axis.plot(poly_points.x, poly_points.y,
                                   **kwargs)[0]
        self.axis.set_xlim(*xlim)
        self.axis.set_ylim(*ylim)
        if refresh:
            plt.draw()

    def legend(self):
        self.axis.legend(self.boxes, self.boxes.index.tolist(), frameon=False)

    @property
    def points(self):
        points = pd.DataFrame([b.get_xy() for b in self.boxes],
                              columns=['x', 'y'], index=self.boxes.index)
        points -= self.init_points[['dx', 'dy']].values
        return points

    def on_pick_event(self, event):
        " Store which text object was picked and were the pick event occurs."

        if event.artist in self.boxes.values:
            self.dragged = self.boxes[self.boxes.values ==
                                      event.artist].index[0]
            self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
        return True

    def on_release_event(self, event):
        " Update text position and redraw"
        if self.dragged is not None and event.xdata is not None:
            box = self.boxes[self.dragged]
            position = event.xdata, event.ydata
            for signal, callback in self.handlers.itervalues():
                if signal == 'box_release_event':
                    callback(box, position)
            self.dragged = None

    def on_mouse_move(self, event):
        if self.dragged is not None and event.xdata is not None:
            box = self.boxes[self.dragged]
            old_pos = box.get_xy()
            new_pos = (old_pos[0] + event.xdata - self.pick_pos[0],
                       old_pos[1] + event.ydata - self.pick_pos[1])
            self.pick_pos = (event.xdata, event.ydata)
            box.set_xy(new_pos)
            for signal, callback in self.handlers.itervalues():
                if signal == 'box_move_event':
                    callback(box, old_pos, new_pos)
            plt.draw()
        return True

    def disconnect(self, handler_id):
        if handler_id in self.handlers:
            del self.handlers[handler_id]

    def connect(self, signal, callback):
        if signal in ('box_move_event', 'box_release_event'):
            self.handlers[self.handler_index] = signal, callback
            handler_index = self.handler_index
            self.handler_index = handler_index + 1
            return handler_index


if __name__ == '__main__':
    # Usage example
    from PIL import Image
    import numpy as np
    import pkg_resources

    # Create arbitrary points and labels
    fig, axes = plt.subplots(2)

    image_path = pkg_resources.resource_filename('matplotlib_helpers',
                                                 'fixtures/testimage.png')
    im = Image.open(image_path)

    axes[0].imshow(np.array(im))
    axes[1].set_xlim(0, 640)
    axes[1].set_ylim(480, 0)
    axes[1].set_aspect('equal')

    # Create the event hendler
    points = [PointsHandler(ax) for ax in axes]

    plt.show()

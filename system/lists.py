#! /usr/bin/python

import clutter
import gobject

QUEUE_MAX = 50

class ScrollingList(clutter.Group):
    def __init__(self, max_height, max_width, font_name):
        clutter.Group.__init__(self)
        self.total_height = 0
        self.max_height = max_height
        self.max_width = max_width
        self.font_name = font_name
        self.set_clip(0, 0, self.max_width, self.max_height)
        self.locked = False
        self.queue = []
        
    def add_text(self, message):
        if self.locked:
            if len(self.queue) < QUEUE_MAX:
                self.queue.append(message)
            return
        text = clutter.Text()
        text.set_font_name(self.font_name)
        text.set_text(message)
        text.set_y(self.total_height)
        self.total_height += text.get_height()
        width = text.get_width()
        self.add(text)
        if self.total_height > self.max_height:
            self.shift_up(self.get_nth_child(0).get_height())

    def shift_up(self, height):
        self.locked = True
        timeline = clutter.Timeline(500)
        alpha = clutter.Alpha(timeline, clutter.LINEAR)
        def make_path(actor, shifts):
            path = clutter.Path()
            x, y = actor.get_position()
            path.add_move_to(int(x), int(y))
            path.add_line_to(int(x), int(y - height))
            shift = clutter.BehaviourPath(alpha, path)
            shift.apply(actor)
            shifts.append(shift)
        shifts = []
        self.foreach(make_path, shifts)
        timeline.connect('completed', self.done_shift, shifts)
        timeline.start()
        self.total_height -= height

    def done_shift(self, timeline, shift):
        self.locked = False
        self.remove(self.get_nth_child(0))
        if(self.queue):
            self.add_text(self.queue.pop(0))


if __name__ == '__main__':

    stage = clutter.Stage()
    stage.set_size(200,200)
    stage.set_color(clutter.color_from_string('dark grey'))

    sl = ScrollingList(100, 100, 'Helvetica 14')

    def add_new(counter):
        sl.add_text("text%d" % counter[0])
        counter[0] = counter[0] + 1
        return True
    counter = [0]
    gobject.timeout_add(100, add_new, counter)

    stage.add(sl)

    stage.connect('destroy', clutter.main_quit)
    stage.show()
    clutter.main()



        






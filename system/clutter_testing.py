#! /usr/bin/python

import clutter
import gobject

stage = clutter.Stage()
stage.set_size(500,500)
stage.set_color(clutter.color_from_string('light blue'))
stage.show()

group = clutter.Group()
group.set_position(100,100)
stage.add(group)

rect = clutter.Rectangle()
rect.set_size(100,200)
rect.set_color(clutter.color_from_string('green'))
group.add(rect)

def animate():
    print 'animating'
    timeline = clutter.Timeline(duration=1000)
    alpha = clutter.Alpha(timeline, clutter.EASE_OUT_BOUNCE)
    behav2 = clutter.BehaviourRotate(clutter.Y_AXIS, 0, 90)
    behav2.set_alpha(alpha)
    behav2.apply(rect)
    timeline.start()

gobject.timeout_add(1000, animate)

stage.connect('destroy', clutter.main_quit)
clutter.main()


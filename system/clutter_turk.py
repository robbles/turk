#! /usr/bin/env python

import clutter
import os

os.chdir('/turk')

def mouse_enter(actor, event, *args):
    global icons
    #actor.animate(clutter.LINEAR, 500, 'rotation-angle-y', 180)
    actor.get_nth_child(0).set_opacity(20)
    for icon in icons:
        if icon is not actor:
            icon.get_nth_child(0).set_opacity(0)


def mouse_leave(actor, event, *args):
    #actor.animate(clutter.LINEAR, 500, 'rotation-angle-y', 0)
    actor.get_nth_child(0).set_opacity(0)


script = clutter.Script()
script.load_from_file('default_stage.js')

stage = script.get_object('stage')

icons = script.get_objects('icon1', 'icon2', 'icon3', 'icon4')

for icon in icons:
    icon.set_reactive(True)
    icon.connect('enter-event', mouse_enter)
    icon.connect('leave-event', mouse_leave)


stage.connect('destroy', clutter.main_quit)
stage.show_all()

clutter.main()


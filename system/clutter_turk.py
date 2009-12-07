#! /usr/bin/env python

import clutter
import os
import dbus
import dbus.service
import dbus.mainloop.glib
from gobject import timeout_add
from time import sleep
from random import randint
from lists import ScrollingList

# Global

TURK_HOME = os.getenv('TURK_HOME')
if not TURK_HOME:
    TURK_HOME = '/turk'

IGNORE_SIGNALS = [
    'NameOwnerChanged',
]

# Main Class
class TurkGUI(dbus.service.Object):
    def __init__(self, bus):
        dbus.service.Object.__init__(self, bus, '/TurkGUI')
        os.chdir('%s/system' % TURK_HOME)
        bus.add_signal_receiver(self.dbus_signal_receive, byte_arrays=True,
                                sender_keyword='sender', destination_keyword='dest',
                                interface_keyword='interface', member_keyword='member',
                                path_keyword='path')

    def draw(self):
        script = clutter.Script()
        script.load_from_file('default_stage.js')

        stage = script.get_object('stage')

        self.grid = Grid(stage, 3, 4, 100, 15)

        self.list = ScrollingList(280, 190, 'Helvetica 12')
        self.list.set_position(490, 20)
        stage.add(self.list)

        stage.connect('destroy', clutter.main_quit)
        stage.show_all()

        # Debugging icons
        """
        for i in range(12):
            pic = ['lamp.png', 'display.png', 'sound.png'][randint(0, 2)]
            timeout_add(1000*i, self.add_icon, 'device', pic)
        """

        clutter.main()

    def add_icon(self, name, imagefile):
        img = clutter.Texture()
        img.set_from_file(imagefile)
        self.grid.add_actor(img)

    def dbus_signal_receive(self, *args, **kw):
        print 'received a D-BUS signal!'
        print kw
        member = kw['member']
        if member == 'NewDriver':
            print 'GUI: showing the new device'
            self.add_icon(args[0], args[1])
        if member not in IGNORE_SIGNALS:
            self.list.add_text(member)


class Grid(object):
    def __init__(self, parent, rows, columns, holder_size, spacing):
        self.holder_size = holder_size
        self.unused_holders = []
        self.group = clutter.Group()
        self.animations = {}
        for y in range(rows):
            for x in range(columns):
                holder = clutter.Group()
                holder.set_size(holder_size, holder_size)
                holder.set_position(spacing + x * (holder_size + spacing),
                                    spacing + y * (holder_size + spacing))
                rect = clutter.Rectangle()
                rect.set_size(holder_size,holder_size)
                rect.set_color(clutter.color_from_string('blue'))
                rect.set_opacity(20)
                rect.set_border_color(clutter.color_from_string('black'))
                rect.set_border_width(2)
                holder.add(rect)
                self.group.add(holder)
                self.unused_holders.insert(0, holder)
        self.parent = parent
        parent.add(self.group)

    def add_actor(self, actor):
        if self.unused_holders:
            holder = self.unused_holders.pop()
            actor.set_size(self.holder_size, self.holder_size)
            start_y = int(holder.get_transformed_position()[1]) + 100
            actor.set_y(-start_y)

            # Animate drop-in
            timeline = clutter.Timeline(duration=1000)
            alpha = clutter.Alpha(timeline, clutter.EASE_OUT_BOUNCE)
            path = clutter.Path()
            path.add_move_to(0, -start_y)
            path.add_line_to(0, 0)
            drop = clutter.BehaviourPath(alpha, path)
            drop.apply(actor)
            timeline.connect('completed', self.animation_done)
            self.animations[timeline] = (drop, holder)
            timeline.start()

            holder.add(actor)

    def animation_done(self, timeline):
        animation, holder = self.animations.pop(timeline)
        holder.remove(holder.get_nth_child(0))



# Main Loop
if __name__ == '__main__':

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    gui = TurkGUI(bus)
    gui.draw()



#! /bin/sh

# Stop TURK system services
killall python

# Shutdown xbee driver
ifconfig zigbee0 down
killall ldisc_daemon
rmmod n_turk

echo "TURK platform offline..."


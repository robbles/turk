#! /bin/sh

# Initialize xbee driver and network interface
insmod /TURK/turk_xbee/n_turk.ko
/TURK/turk_xbee/ldisc_daemon
ifconfig zigbee0 10.0.0.0 up

# Start TURK system services
/TURK/mapper.py
/TURK/spawner.py

echo "TURK platform is now running"


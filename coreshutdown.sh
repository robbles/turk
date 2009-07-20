#! /bin/sh

# Stop TURK system services
echo "Sending TERM signal to all Turk Core processes"
pkill -TERM -f mapper
pkill -TERM -f spawner
pkill -TERM -f bridge

# Just to be extra paranoid....
killall python

echo "TURK Core stopped"


#! /bin/sh

# Stop TURK system services
pkill -f "mapper\(.py\)\?"
pkill -f "spawner\(.py\)\?"

echo "TURK Core stopped"


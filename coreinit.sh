#! /bin/sh

CALLPATH=$(pwd)
COREPATH=$(dirname $0)

cd $COREPATH

# Start TURK system services
./mapper.py
./spawner.py
./bridge.py &

cd $CALLPATH

echo "TURK Core started successfully"


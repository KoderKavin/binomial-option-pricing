#!/bin/bash
# run_terminal.sh - Helper script to launch ThetaTerminal

THETA_DIR="/home/darkside/ThetaTerminal"
JAR_FILE="$THETA_DIR/ThetaTerminalv3.jar"

if [ ! -f "$JAR_FILE" ]; then
    echo "Error: ThetaTerminalv3.jar not found in $THETA_DIR"
    exit 1
fi

echo "Starting ThetaTerminal REST API v3 from $THETA_DIR..."
cd "$THETA_DIR" && java -jar ThetaTerminalv3.jar

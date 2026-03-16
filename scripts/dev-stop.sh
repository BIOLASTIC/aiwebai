#!/bin/bash

if [ -f ".dev.pids" ]; then
    while read pid; do
        echo "Stopping process $pid..."
        kill $pid || true
    done < .dev.pids
    rm .dev.pids
fi

echo "Stopping docker compose..."
docker compose stop || true

echo "All processes stopped."

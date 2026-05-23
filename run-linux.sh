#!/usr/bin/env bash
# Boost chiaki-ng process priority once it launches, then start the bridge
(
    for _ in $(seq 1 30); do
        PID=$(pgrep -i "chiaki" 2>/dev/null | head -1)
        if [ -n "$PID" ]; then
            renice -n -5 -p "$PID" 2>/dev/null || true
            break
        fi
        sleep 2
    done
) &

python3 destiny1-mk-linux.py

#!/bin/bash

echo "[truefan] Starting..."
echo "[truefan] Checking for sensors..."

# Wait for /sys/class/hwmon to exist
for i in {1..5}; do
  if [ -d /sys/class/hwmon ]; then
    echo "[truefan] hwmon devices found."
    break
  fi
  echo "[truefan] Waiting for hwmon devices... ($i/5)"
  sleep 1
done

# Optionally check that at least one sensor shows data
if ! sensors | grep -q .; then
  echo "[truefan] WARNING: No sensor data detected."
fi

echo "[truefan] Launching app..."
exec python3 server.py

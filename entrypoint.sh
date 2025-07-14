#!/bin/bash

echo "[truefan] Starting..."
echo "[truefan] Checking for sensors..."

for i in {1..5}; do
  if [ -d /sys/class/hwmon ]; then
    echo "[truefan] hwmon devices found."
    break
  fi
  echo "[truefan] Waiting for hwmon devices... ($i/5)"
  sleep 1
done

if ! sensors | grep -q .; then
  echo "[truefan] WARNING: No sensor data detected."
fi

echo "[truefan] Launching with gunicorn..."
exec gunicorn -w 2 -b 0.0.0.0:5002 server:app

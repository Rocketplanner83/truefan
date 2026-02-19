TrueFan

TrueFan is a lightweight web application and Dockerized service for monitoring and controlling system fans using lm-sensors and PWM.

It provides:
    •    A simple dashboard with temperature and fan RPM charts
    •    Auto-refreshing UI (live updates)
    •    Profile management (Silent, Cool, Aggressive)
    •    Manual PWM slider control
    •    Export of sensor data to CSV
    •    Container management actions (restart, shutdown)

✨ Features
    •    Web Dashboard: CPU load, uptime, temperatures, and fan speeds
    •    Profiles: Switch between Silent, Cool, and Aggressive, with active profile highlighting
    •    Manual PWM: Apply PWM via slider
    •    Dark Mode: UI theme toggle
    •    Backend Routes:
    •    /sensors → JSON of temps/fans
    •    /status → uptime, load, active profile
    •    /pwm/<value> → set PWM directly
    •    /set/<profile> → switch fan profile
    •    /restart-container → reboot container
    •    /shutdown-container → shutdown container

📸 Dashboard Preview
    •    Status: uptime, load averages, active profile
    •    Fan Profiles: one-click switching with highlighting
    •    PWM Control: manual slider (0–255)
    •    Graphs: live fan RPMs & temperatures with Chart.js

Access at:

http://<host-ip>:5002

🐳 Docker Usage

Run from Docker Hub

docker run -d \
  --name truefan \
  -p 5002:5002 \
  -v /sys/class/hwmon:/sys/class/hwmon:ro \
  -v /dev/sda:/dev/sda:ro \
  -v /etc/sensors3.conf:/etc/sensors3.conf:ro \
  rocketplanner83/truefan:latest

Build from Source

git clone https://github.com/Rocketplanner83/truefan.git
cd truefan
docker build -t rocketplanner83/truefan:latest .

Docker Compose

docker compose up -d

Architecture note:
    •    truefan-core runs in monitoring-first mode.
    •    Hardware writes are delegated to the local truefan-control agent.
    •    If the agent is unavailable, the core API remains available in monitoring-only mode.

Access the dashboard:
    •    Local: http://localhost:5002
    •    LAN: http://192.168.x.x:5002

🔧 Development

Rebuild after changes:

docker compose build --no-cache truefan
docker compose up -d

View logs:

docker logs -f truefan

🚀 Roadmap
    •    Custom profile editor in the UI
    •    Export/import profile configurations
    •    Improved mobile view
    •    Integration with Prometheus/Grafana

📜 License

MIT License. See LICENSE for details.

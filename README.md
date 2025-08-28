TrueFan

TrueFan is a lightweight web application and Dockerized service for monitoring and controlling system fans using lm-sensors and PWM.

It provides:
    •    A simple dashboard with temperature and fan RPM charts
    •    Auto-refreshing UI (live updates)
    •    Profile management (Silent, Cool, Aggressive)
    •    Manual PWM slider control
    •    Export of sensor data to CSV
    •    Container management actions (restart, shutdown)

Features
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

Installation

Clone the repository:

git clone https://github.com/Rocketplanner83/truefan.git
cd truefan

Build the Docker image:

docker build -t rocketplanner83/truefan:latest .

Or use the prebuilt image:

docker pull rocketplanner83/truefan:latest

Usage

Run with Docker Compose:

docker compose up -d

Access the dashboard:

http://localhost:5002

Or via LAN:

http://192.168.x.x:5002

Development

Rebuild after changes:

docker compose build --no-cache truefan
docker compose up -d

Logs:

docker logs -f truefan

Roadmap
    •    Custom profile editor in the UI
    •    Export/import profile configurations
    •    Improved mobile view
    •    Integration with Prometheus/Grafana

License

MIT License. See LICENSE for details.

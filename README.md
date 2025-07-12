# 🌀 truefan


A lightweight Flask-based fan controller dashboard for Linux servers. Displays temperature, fan RPM, and lets you switch fan profiles with optional automatic or manual PWM control.

## 🔧 Features

- Real-time CPU temperature and fan RPM monitoring
- Fan speed chart with Chart.js
- Rotating SVG fan icons based on live RPM
- Profile switching (silent, cool, aggressive)
- Manual fan control trigger
- Container restart/shutdown buttons
- Auto and manual dark mode with persistence
- Dockerized for easy deployment

## 🚀 Getting Started

### Prerequisites

- Linux system with `lm-sensors` installed and configured
- Docker + Docker Compose (or use Dockge/Portainer)

### Clone and Run

```bash
git clone https://github.com/rocketplanner83/truefan.git
cd truefan
docker compose up -d



services:
  truefan:
    image: rocketplanner83/truefan:latest
    container_name: truefan
    restart: unless-stopped
    privileged: true
    working_dir: /app
    ports:
      - "5002:5002"
    environment:
      - TZ=America/Chicago
    volumes:
      - /sys:/sys
      - /dev:/dev
      - /etc/sensors3.conf:/etc/sensors3.conf:ro

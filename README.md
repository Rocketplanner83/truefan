# 🌀 truefan

[![Deploy with Dockge](https://dockge.com/deploy-button.svg)](https://dockge.com/deploy?repo=https://github.com/Rocketplanner83/truefan.git)

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

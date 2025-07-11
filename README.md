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
- Python 3.7+
- Docker + Docker Compose

### Clone and Run

```bash
git clone https://github.com/YOUR_USERNAME/truefan.git
cd truefan
docker-compose up --build -d

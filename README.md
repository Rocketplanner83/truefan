📦 Release Notes – v0.2.0
Highlights
✨ Web UI improvements:
Auto-refresh of status, temps, and fan speeds every few seconds
Active profile button now highlights in green
Cleaner dashboard rendering using Chart.js
⚡ Backend updates:
Added /set/<profile> endpoint for easier fan profile changes (silent, cool, aggressive)
Improved /status endpoint with uptime + load averages
Fixed duplicate Flask route bug that was breaking the container
🛠 General improvements:
Safer entrypoint with better sensor detection logging
Dockerfile and entrypoint cleaned up for reliability
Updated documentation and setup instructions
📘 Updated README.md
Here’s a suggested complete replacement for your README:
# TrueFan

**TrueFan** is a lightweight fan controller dashboard built with **Flask** and **Chart.js**, packaged for Docker.  
It provides a clean web UI for monitoring system temperatures and fans, setting profiles, and managing container state.

---

## 🚀 Features
- Real-time fan speed and temperature monitoring
- Profile switching (`silent`, `cool`, `aggressive`)
- Manual PWM control
- Auto-refreshing dashboard with active profile highlighting
- Container restart/shutdown from the web UI
- Export sensor data as CSV

---

## 🖥 Web UI
Access the dashboard at:

http://<host-ip>:5002

### Example
- **Status**: uptime, load averages, active profile  
- **Fan Profiles**: one-click switching with highlighting  
- **PWM Control**: manual slider (0–255)  
- **Graphs**: live fan RPMs & temperatures with Chart.js  

---

## 🐳 Docker Usage

### Run from Docker Hub
```bash
docker run -d \
  --name truefan \
  --privileged \
  -p 5002:5002 \
  -v /sys:/sys \
  -v /dev:/dev \
  -v /etc/sensors3.conf:/etc/sensors3.conf:ro \
  rocketplanner83/truefan:latest
```

Build from source
git clone https://github.com/Rocketplanner83/truefan.git
cd truefan
docker build -t rocketplanner83/truefan:latest .
docker run -d --name truefan ... rocketplanner83/truefan:latest
📡 API Endpoints
/ → Dashboard UI
/status → JSON with profile, uptime, load
/sensors → JSON fan RPMs & temps
/set/<profile> → POST to change profile (silent, cool, aggressive)
/pwm/<value> → POST to set PWM manually (0–255)
/restart-container → Restart the container
/shutdown-container → Shutdown host
🔖 Versions
v0.2.0: Auto-refresh, active profile highlighting, new /set/<profile> API
v0.1.9: Initial public version with basic UI and fan control
⚠️ Notes
Requires lm-sensors support on host
Must run in --privileged mode for /dev access
Developed & tested on Linux with ZFS-based homelab
📜 License
MIT


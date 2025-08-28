from flask import Flask, jsonify, send_from_directory
import subprocess
import os
import re

# Tell Flask where templates and static live
app = Flask(__name__, static_folder="static", template_folder="templates")


def get_profile():
    raw = subprocess.getoutput("python3 fan.py get-profile")
    # Clean up whitespace and duplicate words
    cleaned = raw.replace("Active profile:", "").strip()
    parts = cleaned.split()
    if len(parts) >= 2 and parts[0] == parts[1]:
        return parts[0].lower()
    return cleaned.lower()




def get_sensors_data():
    output = subprocess.getoutput("sensors")
    fans, temps = {}, {}
    for line in output.splitlines():
        fan_match = re.match(r"(fan\d+):\s+(\d+)\s+RPM", line)
        if fan_match:
            fans[fan_match[1]] = f"{fan_match[2]} RPM"
        temp_match = re.match(r"([\w\-]+):\s+\+?([0-9.]+)°?C", line)
        if temp_match:
            temps[temp_match[1]] = f"{temp_match[2]}°C"
    return fans, temps


def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def get_cpu_load():
    load1, load5, load15 = os.getloadavg()
    return {
        '1min': round(load1, 2),
        '5min': round(load5, 2),
        '15min': round(load15, 2),
    }


# --- Routes ---

@app.route('/')
def index():
    # Serve the dashboard from /app/templates/index.html
    return send_from_directory(app.template_folder, 'index.html')


@app.route('/sensors')
def sensors():
    fans, temps = get_sensors_data()
    return jsonify({'fans': fans, 'temps': temps})


@app.route('/pwm/<value>', methods=['POST'])
def set_pwm(value):
    subprocess.Popen(['python3', 'fan.py', 'set', value])
    return jsonify({'status': 'ok'})


@app.route('/set/<profile>', methods=['POST'])
def set_profile(profile):
    subprocess.Popen(['python3', 'fan.py', 'set-profile', profile])
    return jsonify({'status': 'ok', 'profile': profile})


@app.route('/restart-container', methods=['POST'])
def restart_container():
    subprocess.Popen(['reboot'])
    return jsonify({'status': 'restarting'})


@app.route('/shutdown-container', methods=['POST'])
def shutdown_container():
    subprocess.Popen(['shutdown', '-h', 'now'])
    return jsonify({'status': 'shutting down'})


@app.route('/status')
def status():
    return jsonify({
        'profile': get_profile(),
        'uptime': get_uptime(),
        'load': get_cpu_load()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)

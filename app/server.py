from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess
import re
import os

app = Flask(__name__)

def get_profile():
    raw = subprocess.getoutput("python3 fan.py get-profile")
    return raw.replace("Active profile:", "").strip()

def get_sensors_data():
    output = subprocess.getoutput("sensors")
    fans = {}
    temps = {}

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

@app.route('/')
def index():
    profile = get_profile()
    fans, temps = get_sensors_data()
    uptime = get_uptime()
    load = get_cpu_load()
    return render_template('index.html', profile=profile, fans=fans, temps=temps, uptime=uptime, load=load)

@app.route('/set/<name>')
def set_profile(name):
    subprocess.call(["python3", "fan.py", "set-profile", name])
    return redirect(url_for('index'))

@app.route('/control')
def control():
    subprocess.call(["python3", "fan.py", "control"])
    return redirect(url_for('index'))

@app.route('/sensors')
def sensors():
    fans, temps = get_sensors_data()
    return jsonify({'fans': fans, 'temps': temps})

@app.route('/restart', methods=["POST"])
def restart():
    subprocess.call(["reboot"])
    return "Restarting...", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)

import os
import json
import subprocess
from datetime import datetime

HWMON_PATH = "/sys/class/hwmon/hwmon4"
PROFILE_FILE = "fan_profile.conf"
LOG_FILE = "logs/fan.log"
PWM_HEADERS = [1, 2, 3, 4]

def read_temp_cpu():
    try:
        out = subprocess.check_output(["sensors"], encoding="utf-8")
        for line in out.splitlines():
            if "Package id 0" in line:
                return int(float(line.split()[3].replace("+", "").replace("°C", "")))
    except:
        return 0

def read_temp_nvme():
    try:
        out = subprocess.check_output(["smartctl", "-A", "/dev/nvme0"], encoding="utf-8")
        for line in out.splitlines():
            if "Temperature:" in line:
                return int(line.split()[1])
    except:
        return 0

def read_temp_hdd():
    try:
        out = subprocess.check_output(["smartctl", "-A", "/dev/sda"], encoding="utf-8")
        for line in out.splitlines():
            if "Temperature_Celsius" in line or "Temperature_Case" in line:
                return int(line.split()[-1])
            if "194 Temperature" in line:
                return int(line.split()[-1])
    except:
        return 0

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return "cool"
    with open(PROFILE_FILE) as f:
        for line in f:
            if line.startswith("profile="):
                return line.strip().split("=")[1]
    return "cool"

def determine_pwm(cpu_temp, profile):
    if profile == "quiet":
        if cpu_temp >= 80: return 180
        elif cpu_temp >= 65: return 120
        else: return 70
    elif profile == "cool":
        if cpu_temp >= 70: return 255
        elif cpu_temp >= 55: return 180
        else: return 100
    elif profile == "aggressive":
        if cpu_temp >= 50: return 255
        elif cpu_temp >= 40: return 180
        else: return 130
    return 120

def set_pwm(pwm):
    for i in PWM_HEADERS:
        try:
            with open(f"{HWMON_PATH}/pwm{i}_enable", "w") as f:
                f.write("1")
            with open(f"{HWMON_PATH}/pwm{i}", "w") as f:
                f.write(str(pwm))
        except:
            continue

def log_status(cpu, nvme, hdd, pwm, profile):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - Profile: {profile} | CPU: {cpu}°C | NVMe: {nvme}°C | HDD: {hdd}°C → PWM: {pwm}\n")

def set_profile(name):
    with open(PROFILE_FILE, "w") as f:
        f.write(f"profile={name}\n")
    print(f"Profile set to: {name}")

def get_profile():
    print(f"Active profile: {load_profile()}")

def control():
    profile = load_profile()
    cpu_temp = read_temp_cpu()
    nvme_temp = read_temp_nvme()
    hdd_temp = read_temp_hdd()
    pwm = determine_pwm(cpu_temp, profile)
    set_pwm(pwm)
    log_status(cpu_temp, nvme_temp, hdd_temp, pwm, profile)
    print(f"Applied profile '{profile}' → PWM: {pwm}")

def status():
    cpu = read_temp_cpu()
    nvme = read_temp_nvme()
    hdd = read_temp_hdd()
    print(f"CPU Temp: {cpu}°C | NVMe Temp: {nvme}°C | HDD Temp: {hdd}°C")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: fan.py [status|control|set-profile <name>|get-profile]")
        exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        status()
    elif cmd == "control":
        control()
    elif cmd == "set-profile" and len(sys.argv) == 3:
        set_profile(sys.argv[2])
    elif cmd == "get-profile":
        get_profile()
    else:
        print("Unknown command.")
import os
import json
import subprocess
from datetime import datetime

HWMON_PATH = "/sys/class/hwmon/hwmon4"
PROFILE_FILE = "fan_profile.conf"
LOG_FILE = "logs/fan.log"
PWM_HEADERS = [1, 2, 3, 4]

def read_temp_cpu():
    try:
        out = subprocess.check_output(["sensors"], encoding="utf-8")
        for line in out.splitlines():
            if "Package id 0" in line:
                return int(float(line.split()[3].replace("+", "").replace("°C", "")))
    except:
        return 0

def read_temp_nvme():
    try:
        out = subprocess.check_output(["smartctl", "-A", "/dev/nvme0"], encoding="utf-8")
        for line in out.splitlines():
            if "Temperature:" in line:
                return int(line.split()[1])
    except:
        return 0

def read_temp_hdd():
    try:
        out = subprocess.check_output(["smartctl", "-A", "/dev/sda"], encoding="utf-8")
        for line in out.splitlines():
            if "Temperature_Celsius" in line or "Temperature_Case" in line:
                return int(line.split()[-1])
            if "194 Temperature" in line:
                return int(line.split()[-1])
    except:
        return 0

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return "cool"
    with open(PROFILE_FILE) as f:
        for line in f:
            if line.startswith("profile="):
                return line.strip().split("=")[1]
    return "cool"

def determine_pwm(cpu_temp, profile):
    if profile == "quiet":
        if cpu_temp >= 80: return 180
        elif cpu_temp >= 65: return 120
        else: return 70
    elif profile == "cool":
        if cpu_temp >= 70: return 255
        elif cpu_temp >= 55: return 180
        else: return 100
    elif profile == "aggressive":
        if cpu_temp >= 50: return 255
        elif cpu_temp >= 40: return 180
        else: return 130
    return 120

def set_pwm(pwm):
    for i in PWM_HEADERS:
        try:
            with open(f"{HWMON_PATH}/pwm{i}_enable", "w") as f:
                f.write("1")
            with open(f"{HWMON_PATH}/pwm{i}", "w") as f:
                f.write(str(pwm))
        except:
            continue

def log_status(cpu, nvme, hdd, pwm, profile):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - Profile: {profile} | CPU: {cpu}°C | NVMe: {nvme}°C | HDD: {hdd}°C → PWM: {pwm}\n")

def set_profile(name):
    with open(PROFILE_FILE, "w") as f:
        f.write(f"profile={name}\n")
    print(f"Profile set to: {name}")

def get_profile():
    print(f"Active profile: {load_profile()}")

def control():
    profile = load_profile()
    cpu_temp = read_temp_cpu()
    nvme_temp = read_temp_nvme()
    hdd_temp = read_temp_hdd()
    pwm = determine_pwm(cpu_temp, profile)
    set_pwm(pwm)
    log_status(cpu_temp, nvme_temp, hdd_temp, pwm, profile)
    print(f"Applied profile '{profile}' → PWM: {pwm}")

def status():
    cpu = read_temp_cpu()
    nvme = read_temp_nvme()
    hdd = read_temp_hdd()
    print(f"CPU Temp: {cpu}°C | NVMe Temp: {nvme}°C | HDD Temp: {hdd}°C")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: fan.py [status|control|set-profile <name>|get-profile]")
        exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        status()
    elif cmd == "control":
        control()
    elif cmd == "set-profile" and len(sys.argv) == 3:
        set_profile(sys.argv[2])
    elif cmd == "get-profile":
        get_profile()
    else:
        print("Unknown command.")

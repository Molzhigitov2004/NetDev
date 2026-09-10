from netmiko import ConnLogOnly
from concurrent.futures import ThreadPoolExecutor, as_completed
from yaml import safe_load
from datetime import datetime
import sys

# Instructions:
# Create YAML file called Devices.yml or Devices.yaml in the same directory as this script
# Devices.yaml should have the list of the devices with parameter relevant to Netmiko
# YAML file format
# R1:
#   device_type: cisco_ios
#   host: 192.168.1.1
#   username: admin
#   password: cisco

print("Please read the instructions in the code prior to using this script")
ans = input("I have read the instructions: [CONFIRM]")

devices_data = None
for yaml_filename in ('Devices.yml', 'Devices.yaml'):
    try:
        with open(yaml_filename) as f:
            devices_data = safe_load(f)
        break
    except FileNotFoundError:
        continue
else:
    print("Neither Devices.yml nor Devices.yaml were found")
    sys.exit(1)

devices = list(devices_data.values())
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

def Backup(device: dict):
    host = device.get("host", "UNKNOWN")
    config_saved = False
    backup_created = False
    connection = ConnLogOnly(**device)
    if connection is None:
        return host, {"error": "Connection failed — see netmiko.log"}

    try:
        connection.enable()
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"ENABLE FAILED: {exception}"}
    
    try:
        connection.save_config()
        config_saved = True
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    try:
        backup = connection.send_command("show running-config")
        idx = backup.find("version ")
        if idx != -1:
            backup = backup[idx:]
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    try:
        connection.disconnect()
    except Exception:
        pass

    try:
        with open(f"Backup_{host}_{timestamp}.txt", "w") as file:
            file.write(backup)
            backup_created = True
    except Exception as exception:
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    result = {
        "Config_saved":config_saved,
        "Backup_Created": backup_created,
    }
    return host, result

results = {}
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(Backup, device) for device in devices]
    for future in as_completed(futures):
        host, output = future.result()
        results[host] = output

print("COMPLETED")
for host, output in results.items():
    print(f"{host}: {output}")
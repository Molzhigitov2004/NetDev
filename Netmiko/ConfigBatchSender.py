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
#
# Create txt file called Configs.txt in the same directory as this script
# This txt file should have all the command you would apply in configuration mode
# Script does not check if the command entered was correct or not
# For this reason it is IMPORTANT to check your set of commands for mistakes
# Script also logs the raw cli exchange per device and stamps it with the date

print("Please read the instructions in the code prior to using this script")
ans = input("I have read the instructions: [CONFIRM]")

save = False
ans = input("Do you want to save new configurations as startup configs? y/n: ")
if ans.lower() == "y":
    save = True

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

# devices_data is a dict keyed by device name, e.g. {"R1": {...}, "R2": {...}}
# convert to a list of param dicts for iteration
devices = list(devices_data.values())

try:
    with open("Configs.txt", "r") as f:
        commands = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Configs.txt is not found")
    sys.exit(1)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

def SendConfigBatch(device: dict):
    host = device.get("host", "UNKNOWN")
    connection = ConnLogOnly(session_log=f"{host}_{timestamp}.log", **device)
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
    
    ConfigsApplied = False
    try:
        connection.send_config_set(commands)
        ConfigsApplied = True
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    ConfigsSaved = False
    try:
        if save:
            connection.save_config()
            ConfigsSaved = True
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

    result = {
        "ConfigsApplied": ConfigsApplied,
        "ConfigsSaved": ConfigsSaved,
    }

    return host, result


results = {}
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(SendConfigBatch, device) for device in devices]
    for future in as_completed(futures):
        host, output = future.result()
        results[host] = output

print("COMPLETED")
for host, output in results.items():
    print(f"{host}: {output}")
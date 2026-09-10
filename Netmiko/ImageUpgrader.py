from netmiko import ConnectHandler, ConnLogOnly, file_transfer
from concurrent.futures import ThreadPoolExecutor, as_completed
from yaml import safe_load
import sys

# Instructions:
# Create YAML file called Devices.yml or Devices.yaml in the same directory
# Devices.yaml should have the list of the devices with parameter relevant to Netmiko
# YAML file format
# R1:
#   device_type: cisco_ios
#   host: 192.168.1.1
#   username: admin
#   password: cisco
print("Please read the instructions in the code prior to using this script")
ans = input("I have read the instructions: [CONFIRM]")

reboot = False

print("Enter filepath to the new OS image below")
filepath = input("filepath: ")

print("Enter with what filename you want to save this file on the network device")
image_filename = input("filename: ")

ans = input("Do you want this script to reboot devices with new image? y/n: ")
if ans.lower() == "y":
    reboot = True

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


def LoadNewImage(device: dict):
    host = device.get("host", "UNKNOWN")

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
        connection.send_config_set(["ip scp server enable"])
    except Exception as exception:
        try: 
            connection.disconnect()
        except:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}
        

    try:
        transfer_dict = file_transfer(
            connection,
            source_file=filepath,
            dest_file=image_filename,
            file_system="flash:",
            direction="put",
            overwrite_file=False,
        )
    except FileNotFoundError as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"FILE NOT FOUND ERROR: {exception}"}
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    bootCommand = "boot system flash " + image_filename
    try:
        connection.send_config_set([bootCommand])
    except Exception as exception:
        try:
            connection.disconnect()
        except Exception:
            pass
        return host, {"error": f"UNEXPECTED ERROR: {exception}"}

    reload_output = None
    if reboot:
        reload_output = connection.send_command_timing("reload")
        if "onfirm" in reload_output or "yes/no" in reload_output.lower():
            reload_output += connection.send_command_timing("\n")

    try:
        connection.disconnect()
    except Exception:
        pass

    result = {
        "transfer": transfer_dict,
        "reload_output": reload_output,
    }
    return host, result


results = {}
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(LoadNewImage, device) for device in devices]
    for future in as_completed(futures):
        host, output = future.result()
        results[host] = output

print("COMPLETED")
for host, output in results.items():
    print(f"{host}: {output}")
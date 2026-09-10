from netmiko import ConnLogOnly
from concurrent.futures import ThreadPoolExecutor, as_completed
from yaml import safe_load
from datetime import datetime
import sys
import csv
import re


# Instructions:
# Create YAML file called Devices.yml or Devices.yaml in the same directory as this script
# Devices.yaml should have the list of the devices with parameters relevant to Netmiko
# YAML file format:
#
# R1:
#   device_type: cisco_ios
#   host: 192.168.1.1
#   username: admin
#   password: cisco
#
# Launch the script. It will return audit results with a timestamp.


print("Please read the instructions in the code prior to using this script")
ans = input("I have read the instructions: [CONFIRM]")


# Load devices from YAML
devices_data = None

for yaml_filename in ("Devices.yml", "Devices.yaml"):
    try:
        with open(yaml_filename) as file:
            devices_data = safe_load(file)
        break
    except FileNotFoundError:
        continue
else:
    print("Neither Devices.yml nor Devices.yaml were found")
    sys.exit(1)


devices = list(devices_data.values())
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


def Audit(device: dict):
    host = device.get("host", "UNKNOWN")

    connection = ConnLogOnly(**device)

    if connection is None:
        return host, {"error": "Connection failed — see netmiko.log"}

    result = {}

    # Enable mode
    try:
        connection.enable()
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"ENABLE FAILED: {exception}"}

    # Show version
    try:
        version = connection.send_command(
            "show version",
            use_textfsm=True
        )
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"SHOW VERSION FAILED: {exception}"}

    result["hostname"] = version[0]["hostname"]
    result["hardware_name"] = version[0]["hardware"]
    result["serial_number"] = version[0]["serial"]
    result["software_image"] = version[0]["software_image"]
    result["uptime"] = version[0]["uptime"]
    result["last_reload_reason"] = version[0]["reload_reason"]

    # Show clock
    try:
        time_object = connection.send_command(
            "show clock",
            use_textfsm=True
        )
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"SHOW CLOCK FAILED: {exception}"}

    clock = (
        f'{time_object[0]["timezone"]} '
        f'{time_object[0]["time"]} '
        f'{time_object[0]["month"]} '
        f'{time_object[0]["day"]} '
        f'{time_object[0]["year"]}'
    )

    result["clock"] = clock

    # CPU utilization
    try:
        cpu_utilization = connection.send_command(
            "show processes cpu | i CPU"
        )
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"CPU CHECK FAILED: {exception}"}

    cpu_utilization = cpu_utilization.split("five minutes: ")[1]

    result["cpu_usage_5min"] = cpu_utilization

    # Processor memory
    try:
        processor_memory = connection.send_command(
            "show memory | i Processor",
            delay_factor=2
        )
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"PROCESSOR MEMORY CHECK FAILED: {exception}"}

    processor_memory = re.search(
        r"Processor\s+\S+\s+(\d+)\s+(\d+)",
        processor_memory
    )

    if processor_memory is None:
        result["cpu_mem_usage"] = "UNKNOWN"
    else:
        total = int(processor_memory.group(1))
        used = int(processor_memory.group(2))
        result["cpu_mem_usage"] = f"{(used / total):.2%}"

    # I/O memory
    try:
        io_memory = connection.send_command(
            "show memory | i I/O",
            delay_factor=2
        )
    except Exception as exception:
        connection.disconnect()
        return host, {"error": f"I/O MEMORY CHECK FAILED: {exception}"}

    io_memory = re.search(
        r"I/O\s+\S+\s+(\d+)\s+(\d+)",
        io_memory
    )

    if io_memory is None:
        result["io_mem_usage"] = "UNKNOWN"
    else:
        total = int(io_memory.group(1))
        used = int(io_memory.group(2))
        result["io_mem_usage"] = f"{(used / total):.2%}"

    # Close connection
    connection.disconnect()

    return host, result


results = {}

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(Audit, device)
        for device in devices
    ]

    for future in as_completed(futures):
        host, data = future.result()
        results[host] = data


# Write audit results to CSV
csv_filename = f"audit_{timestamp}.csv"

fieldnames = [
    "ip_address",
    "hostname",
    "hardware_name",
    "serial_number",
    "software_image",
    "uptime",
    "last_reload_reason",
    "clock",
    "cpu_usage_5min",
    "cpu_mem_usage",
    "io_mem_usage"
]

with open(csv_filename, "w", newline="") as csv_file:
    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for host, data in results.items():
        data["ip_address"] = host
        writer.writerow(data)


print(f"Audit completed. Results saved to {csv_filename}")
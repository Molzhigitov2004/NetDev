from netmiko import ConnectHandler, NetmikoAuthenticationException, NetMikoTimeoutException
from getpass import getpass
from threading import Thread
from datetime import datetime
from yaml import safe_load
import sys

# IMPORTANT: Script does not check if your commands were correct, it just sends them

# Guide
# Create file called CliCommands.txt and write down there all commands you want to send
# Create file called Devices.yml and write down all devices you want send commands to
# Launch script and follow prompt
# See the results

# YAML file format
# R1:
#   device_type: cisco_ios
#   host: 192.168.1.1
#   username: admin
#   password: cisco

for filename in ('Devices.yml', 'Devices.yaml'):
    try:
        with open(filename) as f:
            devices = safe_load(f)
        break
    except FileNotFoundError:
        continue
else:
    print("Devices.yml or Devices.yaml is not found")
    sys.exit(1)

try:
    with open("CliCommands.txt", "r") as f:
        commands = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("CliCommands.txt is not found")
    sys.exit()

print("Before starting enter your default credentials")
print("These credentials will be applied if there is no credentials in YAML file")
default_username = input("Enter your username: ")
default_password = getpass()

for hostname in devices.keys():
    devices[hostname].setdefault("username", default_username)
    devices[hostname].setdefault("password", default_password)

results = {}
timeCurrent = datetime.now().strftime("%H.%M.%S_%d.%m.%Y")

for hostname in devices.keys():
    results[hostname] = True  # True means config not applied


def SendCommandsBatch(hostname: str, device: dict):  # saves running configs on the device and issues backup
    try:
        with ConnectHandler(**device) as net_connect:
            net_connect.enable()
            net_connect.save_config()

            backup = net_connect.send_command("show startup-config")
            with open(f"backup_before__{hostname}_{timeCurrent}.txt", "w") as file:
                file.write(backup)

            output_logs = ""
            for command in commands:
                output_logs = output_logs + command + "\n" + net_connect.send_command_timing(command)
            net_connect.save_config()

            with open(f"applied_commands_{hostname}_{timeCurrent}.txt", "w") as file:
                file.write(output_logs)
    except Exception as e:
        print(e)
        return

    results[hostname] = False


Processes = []
for hostname in devices.keys():
    Processes.append(Thread(target=SendCommandsBatch, args=(hostname, devices[hostname])))
for process in Processes:
    process.start()
for process in Processes:
    process.join()


print("Script completed")
print("Results:")
for hostname in results.keys():
    print(f"\033[91m{hostname}: FAILED\033[0m" if results[hostname] else f"\033[92m{hostname}: SUCCESS\033[0m")
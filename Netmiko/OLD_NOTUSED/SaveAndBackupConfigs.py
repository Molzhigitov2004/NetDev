from netmiko import ConnectHandler
from getpass import getpass
from threading import Thread
from datetime import datetime

print("Before starting enter your credentials")
ThisUser = input("Enter your username: ")
ThisPass = getpass()

devices = {  # Enter your devices here
    "EDGE_R1": {
        "device_type": "cisco_ios",
        "host": "192.168.0.142",
        "username": ThisUser,
        "password": ThisPass,
    },

    "EDGE_R2": {
        "device_type": "cisco_ios",
        "host": "192.168.0.224",
        "username": ThisUser,
        "password": ThisPass,
    }
}

results = {}
timeCurrent = datetime.now().strftime("%H.%M.%S_%d.%m.%Y")

for hostname in devices.keys():
    results[hostname] = True  # True means config not yet applied


def SaveBackup(hostname: str, device: dict):  # saves running configs on the device and issues backup
    try:
        with ConnectHandler(**device) as net_connect:
            net_connect.enable()  # get into priv. exec mode
            net_connect.save_config()
            backup = net_connect.send_command("show startup-config")
            with open(f"Backup_{hostname}_{timeCurrent}.txt", "w") as file:
                file.write(backup)
    except Exception as e:
        print(e)
        return

    results[hostname] = False  # False means config was applied


Processes = []
for hostname in devices.keys():
    Processes.append(Thread(target=SaveBackup, args=(hostname, devices[hostname])))
for process in Processes:
    process.start()
for process in Processes:
    process.join()


print("Script completed")
print("Results:")
for hostname in results.keys():
    print(f"\033[91m{hostname}: FAILED\033[0m" if results[hostname] else f"\033[92m{hostname}: SUCCESS\033[0m")
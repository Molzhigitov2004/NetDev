#! /usr/bin/env python3

from ncclient import manager
connection = manager.connect(
    host = '192.168.0.138',
    port = 22,
    username = 'cisco',
    password = 'cisco',
    hostkey_verify = False,
    device_params = {'name':'nexus'},
    look_for_keys = False
)

for value in connection.server_capabilities:
    print(value)
connection.close_session()
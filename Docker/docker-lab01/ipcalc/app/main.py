"""ipcalc API - a tiny subnet calculator for network engineers."""
import ipaddress
import socket

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    return {"status": "ok", "host": socket.gethostname()}


@app.get("/subnet/<path:prefix>")
def subnet(prefix):
    try:
        net = ipaddress.ip_network(prefix, strict=False)
    except ValueError as err:
        return jsonify(error=str(err)), 400
    hosts = list(net.hosts())
    return jsonify(
        network=str(net.network_address),
        prefixlen=net.prefixlen,
        netmask=str(net.netmask),
        wildcard=str(net.hostmask),
        broadcast=str(net.broadcast_address) if net.version == 4 else None,
        first_host=str(hosts[0]) if hosts else None,
        last_host=str(hosts[-1]) if hosts else None,
        usable_hosts=len(hosts),
    )

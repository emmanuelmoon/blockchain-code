# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 23:29:20 2025

@author: Administrator
"""

import socket

# Server addresses and ports
SERVERS = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5002)

]
MESSAGE = "Hello from Client"
def send_message(server_host, server_port):
    """Connect to a server and send a message."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_host, server_port))
        client.send(MESSAGE.encode())
        response = client.recv(1024).decode()
        print(f"Response from {server_host}:{server_port} -> {response}")
    except ConnectionRefusedError:
        print(f"Could not connect to {server_host}:{server_port}")
    finally:
        client.close()

# Send message to all servers
for host, port in SERVERS:
    send_message(host, port)

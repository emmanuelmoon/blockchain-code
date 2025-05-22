# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 23:27:53 2025

@author: Administrator
"""

import socket

HOST = "127.0.0.1"
PORT = 5002  # Unique port for Server 2

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER 2] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        data = conn.recv(1024).decode()
        print(f"[SERVER 2] Received: {data}")
        conn.send(f"Server 2 Response: {data}".encode())

start_server()

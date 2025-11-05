import socket

HOST = ""  # The server's hostname or IP address
PORT = 62435  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    data = []
    s.sendall(b"Hello, world")
    data.append(s.recv(1024))
    s.sendall(b"Testing")
    data.append(s.recv(1024))
    s.sendall(b"More testing")
    data.append(s.recv(1024))

print(f"Received {b', '.join(data)!r}")

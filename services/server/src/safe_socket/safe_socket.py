import socket


def recv_all(socket: socket.socket, size):
    bytes_read = socket.recv(size)
    while len(bytes_read) < size:
        bytes_read += socket.recv(size - len(bytes_read))
    return bytes_read

def send_all(socket: socket.socket, data):
    bytes_sent = socket.send(data)
    while bytes_sent < len(data):
        bytes_sent += socket.send(data[bytes_sent:])

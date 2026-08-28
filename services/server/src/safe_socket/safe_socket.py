import socket

# TODO: Complete with a short-read/short-write tolerant implementation


def recv_all(socket: socket.socket, size):
    bytes_read = socket.recv(size)
    while len(bytes_read) < size:
        bytes_read += socket.recv(size - len(bytes_read))
    return bytes_read

def send_all(socket: socket.socket, bytes):
    bytes_sent = socket.send(bytes)
    while bytes_sent < len(bytes):
        bytes_sent += socket.send(bytes[bytes_sent:])

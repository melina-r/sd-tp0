import socket

def recv_all(sock: socket.socket, size: int) -> bytes:
    """Receives a specified number of bytes from the socket, 
    ensuring that all bytes are received."""
    data = bytearray()
    while len(data) < size:
        bytes_recv = sock.recv(size - len(data))
        if not bytes_recv:
            raise ConnectionError("Socket connection closed while receiving data.")
        data.extend(bytes_recv)
    return bytes(data)

def send_all(sock: socket.socket, data: bytes):
    """Sends all bytes of the given data through the socket, 
    ensuring that all bytes are sent."""
    total_sent = 0
    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        total_sent += sent

import socket

def recv_all(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:  # En recv(), un retorno de b"" si significa fin de stream / socket cerrado
            raise ConnectionError("El socket se cerró antes de recibir todos los datos")
        data.extend(packet)
    return bytes(data)

def send_all(sock: socket.socket, data: bytes):
    total_sent = 0
    while total_sent < len(data):
        sent = sock.send(data[total_sent:])
        total_sent += sent  # Si sent == 0, simplemente suma 0 y reintenta en el siguiente ciclo
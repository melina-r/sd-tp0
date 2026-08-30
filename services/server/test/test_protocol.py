import socket
import unittest

from lottery import Bet
from protocol.deserializer import deserialize_bet
from protocol.serializer import serialize_bet, serialize_end_of_transmission
from src.server.server import Server


class ProtocolTests(unittest.TestCase):
    def test_serialize_bet_has_total_length_prefix(self):
        bet = Bet(1, "Ana", "Perez", 12345678, "1990-01-01", 7574)

        payload = serialize_bet(bet)

        self.assertGreaterEqual(len(payload), 4)
        total_length = int.from_bytes(payload[:4], byteorder="big")
        self.assertEqual(total_length, len(payload) - 4)

    def test_serialize_and_deserialize_bet_round_trip(self):
        bet = Bet(1, "Ana", "Perez", 12345678, "1990-01-01", 7574)

        payload = serialize_bet(bet)
        decoded = deserialize_bet(payload[4:])

        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.agency_id, bet.agency_id)
        self.assertEqual(decoded.first_name, bet.first_name)
        self.assertEqual(decoded.last_name, bet.last_name)
        self.assertEqual(decoded.document, bet.document)
        self.assertEqual(decoded.birthdate, bet.birthdate)
        self.assertEqual(decoded.number, bet.number)

    def test_deserialize_bet_detects_end_of_transmission(self):
        payload = serialize_end_of_transmission()

        decoded = deserialize_bet(payload[4:])

        self.assertIsNone(decoded)

    def test_recv_data_and_deserialize_bet_over_socket_pair(self):
        server = Server("127.0.0.1", 0)
        client_sock, server_sock = socket.socketpair()

        try:
            bet = Bet(1, "Ana", "Perez", 12345678, "1990-01-01", 7574)
            client_sock.sendall(serialize_bet(bet))
            client_sock.sendall(serialize_end_of_transmission())

            received_bet = server.recv_data(server_sock)
            decoded_bet = deserialize_bet(received_bet)
            self.assertIsNotNone(decoded_bet)
            self.assertEqual(decoded_bet.first_name, bet.first_name)
            self.assertEqual(decoded_bet.last_name, bet.last_name)
            self.assertEqual(decoded_bet.document, bet.document)
            self.assertEqual(decoded_bet.birthdate, bet.birthdate)
            self.assertEqual(decoded_bet.number, bet.number)

            received_eot = server.recv_data(server_sock)
            self.assertIsNone(deserialize_bet(received_eot))
        finally:
            client_sock.close()
            server_sock.close()


if __name__ == "__main__":
    unittest.main()

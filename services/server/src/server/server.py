import socket
from logger import logger
from safe_socket import recv_all, send_all
from protocol.deserializer import deserialize_bet
from lottery import Lottery
from protocol.serializer import serialize_bet, serialize_end_of_transmission

_TOTAL_LENGTH_SIZE = 4


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery("lottery_storage.csv")

    def recv_data(self, client_socket):
        action = "recv-message"
        try:
            length = recv_all(client_socket, _TOTAL_LENGTH_SIZE)
        except Exception as e:
            logger.error(action, logger.LogResult.fail)
            raise e

        if int.from_bytes(length, byteorder="big") < 1:
            return None

        try:
            data = recv_all(client_socket, int.from_bytes(length, byteorder="big"))
        except Exception as e:
            logger.error(action, logger.LogResult.fail)
            raise e

        return data

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        bets = []
        try:
            while True:
                data = self.recv_data(client_socket)
                if data is None:
                    break

                bet = deserialize_bet(data)
                if bet is None:
                    break

                message_amount += 1
                bets.append(bet)

        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e

        self.lottery.store_bets(bets)

        for bet in bets:
            if self.lottery.has_won(bet):
                data = serialize_bet(bet)
                try:
                    send_all(client_socket, data)
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    raise e
        send_all(client_socket, serialize_end_of_transmission())

    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

                self._handle_client(client_socket)

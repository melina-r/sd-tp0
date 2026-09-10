import socket
import os
import threading
from threading import Lock, Barrier, Event
from logger import logger
from safe_socket import recv_all, send_all
from protocol.deserializer import deserialize_batch
from lottery import Lottery
from protocol.serializer import serialize_batch
from protocol.utils import INT_SIZE

_TOTAL_LENGTH_SIZE = 4
AGENCY_QUORUM_MIN = int(os.getenv('AGENCY_QUORUM_MIN', '3'))


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery("lottery_storage.csv")
        self.storage_lock = Lock()
        self.quorum = Barrier(AGENCY_QUORUM_MIN)
        self.reset_quorum = Barrier(AGENCY_QUORUM_MIN)
        self.results = Event()
        self.winners_lock = Lock()
        self.winners = []

    def safe_load_bets(self):
        with self.storage_lock, self.winners_lock:
            bets = list(self.lottery.load_bets())
            for bet in bets:
                if self.lottery.has_won(bet):
                    self.winners.append(bet)
            self.results.set()

    def get_winners(self, agency_id):
        with self.winners_lock:
            return [bet for bet in self.winners if bet.agency_id == agency_id]

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

    def store_bets_safe(self, bets):
        with self.storage_lock:
            self.lottery.store_bets(bets)

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        agency_id = None
        bets = []

        logger.info(action, logger.LogResult.in_progress)
        try:
            while True:
                data = self.recv_data(client_socket)
                if data is None:
                    break

                agency_id = int.from_bytes(data[:INT_SIZE], byteorder="big")

                action = "recv_batch"
                logger.info(action, logger.LogResult.in_progress, "agency-id", agency_id)
                bets_recv, eot = deserialize_batch(data[INT_SIZE:])
                
                logger.info(action, logger.LogResult.success, "agency-id", agency_id)

                ack = b"1"
                send_all(client_socket, ack)
                logger.info("send-ack", logger.LogResult.success, "agency-id", agency_id, "ack", ack)

                message_amount += 1
                bets.extend(bets_recv)

                if eot:
                    logger.info("recv-eot", logger.LogResult.success, "agency-id", agency_id)
                    break

        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            client_socket.close()
            return

        logger.info(action, logger.LogResult.success, "messages-amount", message_amount)
        
        # Guardado concurrente seguro
        logger.info("store-bets", logger.LogResult.in_progress, "agency-id", agency_id)
        self.store_bets_safe(bets)
        logger.info("store-bets", logger.LogResult.success, "agency-id", agency_id, "bets-stored", len(bets))
        
        # Coordinación del Quórum
        try:        
            logger.info("quorum-wait", logger.LogResult.in_progress, "agency-id", agency_id)
            order = self.quorum.wait()
            logger.info("quorum-wait", logger.LogResult.success, "agency-id", agency_id, "order", order)
        except Exception as e:
            logger.error("quorum-wait", logger.LogResult.fail, "agency-id", agency_id)
            client_socket.close()
            return

        # El primer hilo en cruzar la barrera efectúa el sorteo central
        if order == 0:
            logger.info("load-bets", logger.LogResult.in_progress, "agency-id", agency_id)
            self.safe_load_bets()
            logger.info("load-bets", logger.LogResult.success, "agency-id", agency_id, "winners-found", len(self.winners))

        # Todos los hilos esperan a que los resultados estén listos
        logger.info("wait-results", logger.LogResult.in_progress, "agency-id", agency_id)
        self.results.wait()
        logger.info("wait-results", logger.LogResult.success, "agency-id", agency_id, "winners-found", len(self.winners))

        # Filtrar solo los ganadores de ESTA agencia
        agency_winners = self.get_winners(agency_id)
        logger.info("filter-winners", logger.LogResult.success, "agency-id", agency_id, "winners-found", len(agency_winners))
        batch_data = serialize_batch(agency_winners)
        try:
            order = self.reset_quorum.wait()  # Esperar a que todos los hilos terminen de filtrar sus ganadores
        except Exception as e:
            logger.error("reset-quorum-wait", logger.LogResult.fail, "agency-id", agency_id)
            client_socket.close()
            return

        if order == 0:
            # Reiniciar el estado del servidor para la próxima corrida
            with self.winners_lock:
                self.winners.clear()
            self.results.clear()
            self.quorum.reset()
            logger.info("reset-server", logger.LogResult.success, "agency-id", agency_id)

        logger.info("send-winners", logger.LogResult.in_progress, "agency-id", agency_id, "winners-found", len(agency_winners))
        send_all(client_socket, batch_data)
        logger.info("send-winners", logger.LogResult.success, "agency-id", agency_id, "winners-found", len(agency_winners))
        client_socket.close()

    def run(self):
        action = "accept-connection"
        threads = []

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    break
                logger.info(action, logger.LogResult.success)

                try:
                    logger.info("start-thread", logger.LogResult.in_progress)
                    t = threading.Thread(target=self._handle_client, args=(client_socket,))
                    threads.append(t)
                    t.start()
                    logger.info("start-thread", logger.LogResult.success)
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    client_socket.close()
        
        for t in threads:
            t.join()
            logger.info("join-thread", logger.LogResult.success)
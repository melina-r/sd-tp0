import os
import signal
import socket
import threading
from threading import Barrier, Event, Lock

from logger import logger
from lottery import Lottery
from protocol.deserializer import deserialize_batch
from protocol.serializer import serialize_acknowledgment, serialize_batch
from protocol.utils import INT_SIZE
from safe_socket import recv_all, send_all

_TOTAL_LENGTH_SIZE = 4
AGENCY_QUORUM_MIN = int(os.getenv("AGENCY_QUORUM_MIN", "3"))


class Server:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery("lottery_storage.csv")

        self.server_socket = None

        self.running = False
        self.storage_lock = Lock()
        self.winners_lock = Lock()

        self.quorum = Barrier(AGENCY_QUORUM_MIN)
        self.reset_quorum = Barrier(AGENCY_QUORUM_MIN)

        self.results = Event()
        self.winners = []

    def shutdown(self, signum=None, frame=None):
        """Shuts down the server gracefully, closing the server
        socket and aborting any waiting threads."""
        if not self.running:
            return
        self.running = False
        logger.info("shutdown", logger.LogResult.in_progress)

        try:
            self.quorum.abort()
            self.reset_quorum.abort()
        except Exception:
            logger.error(
                "shutdown", logger.LogResult.fail, "message", "error-aborting-barriers"
            )

        self.results.set()

        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                logger.error(
                    "shutdown",
                    logger.LogResult.fail,
                    "message",
                    "error-shutting-down-socket",
                )
            finally:
                self.server_socket.close()

    def store_bets_safe(self, bets, agency_id):
        """Stores bets in a thread-safe manner."""
        logger.info("store-bets", logger.LogResult.in_progress, "agency-id", agency_id)
        with self.storage_lock:
            self.lottery.store_bets(bets)
        logger.info("store-bets", logger.LogResult.success, "agency-id", agency_id)

    def safe_load_bets(self):
        """Loads bets from storage and determines winners in a thread-safe manner."""
        with self.storage_lock, self.winners_lock:
            bets = list(self.lottery.load_bets())
            for bet in bets:
                if self.lottery.has_won(bet):
                    self.winners.append(bet)
            self.results.set()

    def get_winners(self, agency_id):
        """Returns a list of winners filtered by the given agency ID in a thread-safe manner."""
        with self.winners_lock:
            return [bet for bet in self.winners if bet.agency_id == agency_id]
        logger.info("get-winners", logger.LogResult.success, "agency-id", agency_id)

    def recv_data(self, client_socket):
        """Receives data from the client socket, first reading the
        total length of the incoming data, then reading the actual
        data based on that length."""

        action = "recv-message"
        try:
            length = recv_all(client_socket, _TOTAL_LENGTH_SIZE)
        except Exception as e:
            logger.error(action, logger.LogResult.fail)
            raise e

        length_int = int.from_bytes(length, byteorder="big")
        if length_int < 1:
            return None

        try:
            data = recv_all(client_socket, length_int)
        except Exception as e:
            logger.error(action, logger.LogResult.fail)
            raise e

        return data

    def get_bets_from_client(self, client_socket):
        """Receives bets from the client socket, handling multiple messages
        and acknowledging each one. Returns the agency ID and a list of bets."""
        action = "recv-bets"
        logger.info(action, logger.LogResult.in_progress)
        message_amount = 0
        agency_id = None
        bets = []

        try:
            data = self.recv_data(client_socket)
            agency_id = int.from_bytes(data[:INT_SIZE], byteorder="big")

            while data is not None:
                bets_recv, eot = deserialize_batch(data[INT_SIZE:])
                send_all(client_socket, serialize_acknowledgment())

                message_amount += 1
                bets.extend(bets_recv)

                if eot:
                    logger.info(
                        "recv-eot", logger.LogResult.success, "agency-id", agency_id
                    )
                    break

                data = self.recv_data(client_socket)

        except Exception:
            client_socket.close()
            return None, []

        logger.info(action, logger.LogResult.success, "messages-amount", message_amount)
        return agency_id, bets

    def send_results_to_client(self, client_socket, agency_id, winners):
        """Sends the results (winners) to the client socket for the given agency ID."""
        action = "send-results"
        logger.info(action, logger.LogResult.in_progress, "agency-id", agency_id)

        serialized_data = serialize_batch(winners)

        logger.info(
            "send-winners",
            logger.LogResult.in_progress,
            "agency-id",
            agency_id,
            "winners-found",
            len(winners),
        )
        try:
            send_all(client_socket, serialized_data)
        except Exception:
            logger.error(action, logger.LogResult.fail, "agency-id", agency_id)
            raise

        logger.info(
            "send-winners",
            logger.LogResult.success,
            "agency-id",
            agency_id,
            "winners-found",
            len(winners),
        )

    def coordinate_quorum(self, agency_id):
        """Coordinates the quorum for the agencies, ensuring that all threads
        reach this point before proceeding."""
        action = "coordinate-quorum"
        logger.info(action, logger.LogResult.in_progress)

        logger.info("quorum-wait", logger.LogResult.in_progress, "agency-id", agency_id)
        order = self.quorum.wait()
        logger.info(
            "quorum-wait",
            logger.LogResult.success,
            "agency-id",
            agency_id,
            "order",
            order,
        )

        if order == 0:
            logger.info(
                "load-bets", logger.LogResult.in_progress, "agency-id", agency_id
            )
            self.safe_load_bets()
            logger.info(
                "load-bets",
                logger.LogResult.success,
                "agency-id",
                agency_id,
                "winners-found",
                len(self.winners),
            )

        logger.info(
            "wait-results", logger.LogResult.in_progress, "agency-id", agency_id
        )
        self.results.wait()
        logger.info(
            "wait-results",
            logger.LogResult.success,
            "agency-id",
            agency_id,
            "winners-found",
            len(self.winners),
        )

    def coordinate_reset_quorum(self, agency_id):
        """Coordinates the reset quorum for the agencies, ensuring that all threads
        reach this point before proceeding to reset the winners and results."""
        action = "coordinate-reset-quorum"
        logger.info(action, logger.LogResult.in_progress)
        order = self.reset_quorum.wait()
        if order == 0:
            with self.winners_lock:
                self.winners.clear()
            self.results.clear()
            self.quorum.reset()
            logger.info(action, logger.LogResult.success, "agency-id", agency_id)

    def _handle_client(self, client_socket):
        """Handles the client connection, receiving bets, storing them,
        coordinating the quorum, and sending results back to the client."""
        action = "handle-client"
        logger.info(action, logger.LogResult.in_progress)

        agency_id, bets = self.get_bets_from_client(client_socket)
        if agency_id is None or not bets:
            logger.error(
                action, logger.LogResult.fail, "message", "failed-to-receive-bets"
            )
            client_socket.close()
            return

        self.store_bets_safe(bets, agency_id)

        try:
            self.coordinate_quorum(agency_id)
        except Exception:
            logger.error("quorum-wait", logger.LogResult.fail, "agency-id", agency_id)
            client_socket.close()
            return

        agency_winners = self.get_winners(agency_id)

        try:
            self.coordinate_reset_quorum(agency_id)
        except Exception:
            logger.error("reset-quorum", logger.LogResult.fail, "agency-id", agency_id)
            client_socket.close()
            return

        try:
            self.send_results_to_client(client_socket, agency_id, agency_winners)
        finally:
            client_socket.close()

    def run(self):
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        action = "accept-connection"
        threads = []

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with self.server_socket as server_socket:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            self.running = True
            while self.running:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except OSError:
                    logger.info(
                        action, logger.LogResult.success, "message", "socket-closed"
                    )
                    break
                except Exception as e:
                    logger.error(action, logger.LogResult.fail, "message", str(e))
                    break
                logger.info(action, logger.LogResult.success)

                try:
                    logger.info("start-thread", logger.LogResult.in_progress)
                    t = threading.Thread(
                        target=self._handle_client, args=(client_socket,)
                    )
                    threads.append(t)
                    t.start()
                    logger.info("start-thread", logger.LogResult.success)
                except Exception as e:
                    logger.error(action, logger.LogResult.fail, "message", str(e))
                    client_socket.close()

        for t in threads:
            t.join()
            logger.info("join-thread", logger.LogResult.success)

        logger.info("shutdown", logger.LogResult.success)

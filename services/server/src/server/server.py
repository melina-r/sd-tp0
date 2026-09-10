import multiprocessing
import socket
import os
from threading import Lock, Barrier, Event
from logger import logger
from safe_socket import recv_all, send_all
from protocol.deserializer import deserialize_batch, deserialize_bet
from lottery import Lottery
from protocol.serializer import serialize_bet
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
        self.restart_quorum = Barrier(AGENCY_QUORUM_MIN)
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
            winners = [bet for bet in self.winners if bet.agency_id == agency_id]
        return winners

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

    def _handle_client(self, client_socket, bets_que, quorum):
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
                for bet in bets_recv:
                    bets.append(bet)

                if eot:
                    logger.info("recv-eot", logger.LogResult.success, "agency-id", agency_id)
                    break


        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount
            )
            raise e
        logger.info(action, logger.LogResult.success, "messages-amount", message_amount)
        for bet in bets:
            bets_que.put(bet)
        
        self.store_bets_safe(bets)
        try:        
            order = self.quorum.wait()
        except Exception as e:
            logger.error("quorum-wait", logger.LogResult.fail, "agency-id", agency_id)
            raise e

        if order == 0:
            logger.info("quorum-wait", logger.LogResult.success, "agency-id", agency_id)
            self.safe_load_bets()

        self.results.wait()
        winners = self.get_winners(agency_id)
            
        batch_data = b"".join(
            serialize_bet(bet)
            for bet in winners
        )
        message = len(batch_data).to_bytes(_TOTAL_LENGTH_SIZE, byteorder="big") + batch_data
        send_all(client_socket, message)
        client_socket.close()


    def store_bets(self, bets_que):
        action = "store-bets"
        logger.info(action, logger.LogResult.in_progress)
        bets = []
        while True:
            bet = bets_que.get()
            if bet is None:
                break
            self.lottery.store_bet(bet)


    def run(self):
        action = "accept-connection"
        threads = []

        queue = multiprocessing.Queue()
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

                try:
                    logger.info("start-process", logger.LogResult.in_progress)
                    p = multiprocessing.Process(target=self._handle_client, args=(client_socket, queue, quorum))
                    threads.append(p)
                    p.start()
                    
                    logger.info("start-process", logger.LogResult.success)
                except Exception as e:
                    logger.error(action, logger.LogResult.fail)
                    client_socket.close()
        
        for t in threads:
            t.join()
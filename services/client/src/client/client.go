package client

import (
	"bufio"
	"encoding/binary"
	"net"
	"os"
	"time"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/protocol"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/logger"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/safe_socket"
)

const CONNECTION_ATTEMPTS_MAX = 3
const CONNECTION_ATTEMPS_DELAY_MS = 200

const TOTAL_LENGTH_SIZE = 4

type ClientConfig struct {
	ServerHost     string
	ServerPort     string
	AgencyId       uint32
	BatchSize      int
	InputFilePath  string
	OutputFilePath string
}

type Client struct {
	conn   net.Conn
	config ClientConfig
}

func NewClient(config ClientConfig) (*Client, error) {
	conn, err := connectToServer(config.ServerHost, config.ServerPort)
	if err != nil {
		logger.Warn("connect-to-server", logger.Fail)
		return nil, err
	}

	client := &Client{conn: conn, config: config}
	return client, nil
}

func connectToServer(host, port string) (net.Conn, error) {
	const action = "connect-to-server"
	var err error
	var conn net.Conn

	logger.Info(action, logger.InProgress)
	for i := range CONNECTION_ATTEMPTS_MAX {
		conn, err = net.Dial("tcp", host+":"+port)
		if err != nil {
			logger.Warn(action, logger.Fail, "attempt", i)
			time.Sleep(CONNECTION_ATTEMPS_DELAY_MS * time.Millisecond)
			continue
		}

		logger.Info(action, logger.Success)
		break
	}

	return conn, err
}

func (client *Client) ReceiveMessage() ([]byte, error) {
	responseBuffer, err := safe_socket.RecvAll(client.conn, TOTAL_LENGTH_SIZE)
	if err != nil {
		return nil, err
	}
	length := binary.BigEndian.Uint32(responseBuffer)
	responseBuffer, err = safe_socket.RecvAll(client.conn, int(length))
	if err != nil {
		return nil, err
	}

	return responseBuffer, nil
}

func (client *Client) ReceiveAcknowledgment() bool {
	responseBuffer, err := safe_socket.RecvAll(client.conn, protocol.ACKNOWLEDGMENT_MESSAGE)
	if err != nil {
		logger.Error("recv-ack", logger.Fail, "err", err)
		return false
	}
	ack := responseBuffer[0]

	if ack == 0 {
		logger.Error("recv-ack", logger.Fail, "err", "acknowledgment with byte 0")
		return false
	}
	return true
}

func (client *Client) SendBatch(batch []byte, messageArgs ...any) error {
	clientMessage := protocol.SerializeBatch(batch, client.config.AgencyId)
	logger.Info("send-batch", logger.InProgress, messageArgs...)
	if err := safe_socket.SendAll(client.conn, clientMessage); err != nil {
		logger.Error("send-message", logger.Fail, messageArgs...)
		return err
	}

	logger.Info("send-batch", logger.Success)
	return nil
}

func (client *Client) Run() error {
	const mainAction = "test-echo-server"
	defer client.conn.Close()

	inputFile, err := os.Open(client.config.InputFilePath)
	if err != nil {
		logger.Error(mainAction, logger.Fail, "err", err)
		return err
	}
	defer inputFile.Close()

	outputFile, err := os.Create(client.config.OutputFilePath)
	if err != nil {
		logger.Error(mainAction, logger.Fail, "err", err)
		return err
	}
	defer outputFile.Close()

	scanner := bufio.NewScanner(inputFile)
	messageId := 0
	batch := []byte{}
	batchSize := 0
	messageArgs := []any{"agency-id", client.config.AgencyId, "message-id", messageId}

	for scanner.Scan() {
		data := scanner.Text()
		bet := &lottery.Bet{}
		err := bet.FromCsvLine(data, client.config.AgencyId)
		if err != nil {
			logger.Error("parse-csv-line", logger.Fail, messageArgs...)
			return err
		}
		clientMessage := protocol.SerializeBet(bet)
		batch = append(batch, clientMessage...)
		batchSize++

		messageId++
		if batchSize >= client.config.BatchSize {
			err := client.SendBatch(batch, messageArgs...)
			if err != nil {
				logger.Error("send-batch", logger.Fail, messageArgs...)
				return err
			}

			logger.Info("recv-response", logger.InProgress, messageArgs...)
			ok := client.ReceiveAcknowledgment()
			for !ok {
				logger.Error("recv-response", logger.Fail, messageArgs...)
				logger.Info("send-batch", logger.InProgress, messageArgs...)

				err := client.SendBatch(batch, messageArgs...)
				if err != nil {
					logger.Error("send-batch", logger.Fail, messageArgs...)
					return err
				}

				logger.Info("recv-response", logger.InProgress, messageArgs...)
				ok = client.ReceiveAcknowledgment()
			}

			batch = []byte{}
			batchSize = 0
			logger.Info("recv-response", logger.Success, messageArgs...)
		}
	}

	if batchSize > 0 {
		err := client.SendBatch(batch, messageArgs...)
		if err != nil {
			logger.Error("send-batch", logger.Fail, messageArgs...)
			return err
		}

		logger.Info("recv-response", logger.InProgress, messageArgs...)
		ok := client.ReceiveAcknowledgment()
		if !ok {
			logger.Error("recv-response", logger.Fail, messageArgs...)
			return nil
		}

		batch = []byte{}
		batchSize = 0
		logger.Info("recv-response", logger.Success, messageArgs...)
	}

	eot := protocol.SerializeEndOfTransmission(client.config.AgencyId)
	if err := safe_socket.SendAll(client.conn, eot); err != nil {
		logger.Error("send-end-of-transmission", logger.Fail)
		return err
	}
	logger.Info("send-end-of-transmission", logger.Success)
	ack := client.ReceiveAcknowledgment()
	if !ack {
		logger.Error("recv-ack", logger.Fail, "err", err)
		return err
	}
	logger.Info("recv-ack", logger.Success)

	logger.Info("recv-winners", logger.InProgress)

	response, err := client.ReceiveMessage()
	if err != nil {
		logger.Error("recv-winners", logger.Fail, "err", err)
		return err
	}

	if len(response) == 0 {
		logger.Info("recv-winners", logger.Fail, "err", "empty response")
		return nil
	}
	winners, _ := protocol.DeserializeBatch(response)
	logger.Info("recv-winners", logger.Success, "winners", len(winners))

	if winners == nil {
		logger.Error("recv-winners", logger.Fail)
		return err
	}

	for _, winner := range winners {
		if _, err := outputFile.WriteString(winner.ToCsvLine() + "\n"); err != nil {
			logger.Error("write-output-file", logger.Fail)
			return err
		}
	}
	logger.Info(mainAction, logger.Success, "winners", len(winners))

	return nil
}

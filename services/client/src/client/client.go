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
	AgencyId       string
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
	for scanner.Scan() {
		messageArgs := []any{"agency-id", client.config.AgencyId, "message-id", messageId}
		data := scanner.Text()
		bet := &lottery.Bet{}
		err := bet.FromCsvLine(data, client.config.AgencyId)
		if err != nil {
			logger.Error("parse-csv-line", logger.Fail, messageArgs...)
			return err
		}
		clientMessage := protocol.SerializeBet(bet)

		if err := safe_socket.SendAll(client.conn, clientMessage); err != nil {
			logger.Error("send-message", logger.Fail, messageArgs...)
			return err
		}

		messageId++
	}

	eot := protocol.SerializeEndOfTransmission()
	if err := safe_socket.SendAll(client.conn, eot); err != nil {
		logger.Error("send-end-of-transmission", logger.Fail)
		return err
	}

	winners := []lottery.Bet{}

	for {
		response, err := client.ReceiveMessage()
		if err != nil {
			logger.Error("recv-response", logger.Fail)
			return err
		}
		winner, endOfTransmission := protocol.DeserializeBet(response)
		if endOfTransmission || winner == nil {
			break
		}
		winners = append(winners, *winner)
	}

	for _, winner := range winners {
		if _, err := outputFile.WriteString(winner.ToCsvLine() + "\n"); err != nil {
			logger.Error("write-output-file", logger.Fail)
			return err
		}
	}

	return nil
}

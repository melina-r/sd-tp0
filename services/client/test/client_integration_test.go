package test

import (
	"net"
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/protocol"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client"
)

func TestClientReceiveMessageAndDeserializeBet(t *testing.T) {
	clientConn, serverConn := net.Pipe()
	defer clientConn.Close()
	defer serverConn.Close()

	client := &client.Client{conn: clientConn}

	bet := &lottery.Bet{
		FirstName:     "Ana",
		LastName:      "Perez",
		Document:      12345678,
		BirthDate:     "1990-01-01",
		LotteryNumber: 7574,
		AgencyId:      "1",
	}

	go func() {
		_, _ = serverConn.Write(protocol.SerializeBet(bet))
		_, _ = serverConn.Write(protocol.SerializeEndOfTransmission())
	}()

	response, err := client.ReceiveMessage()
	if err != nil {
		t.Fatalf("ReceiveMessage returned error: %v", err)
	}

	winner, endOfTransmission := protocol.DeserializeBet(response)
	if endOfTransmission {
		t.Fatal("expected a winner payload, got end-of-transmission")
	}
	if winner == nil {
		t.Fatal("winner should not be nil")
	}
	if winner.FirstName != bet.FirstName || winner.LastName != bet.LastName {
		t.Fatalf("winner mismatch: got %s %s want %s %s", winner.FirstName, winner.LastName, bet.FirstName, bet.LastName)
	}

	response, err = client.ReceiveMessage()
	if err != nil {
		t.Fatalf("second ReceiveMessage returned error: %v", err)
	}

	winner, endOfTransmission = protocol.DeserializeBet(response)
	if !endOfTransmission {
		t.Fatal("expected end-of-transmission after winner payload")
	}
	if winner == nil {
		t.Fatal("EOT payload should still produce a valid bet object")
	}
}

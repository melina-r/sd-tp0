package test

import (
	"encoding/binary"
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/protocol"
)

func TestSerializeStringEncodesFieldTypeAndLength(t *testing.T) {
	data := protocol.SerializeString(protocol.FieldTypeName, "Ana")

	if len(data) != protocol.TYPE_SIZE+protocol.LENGTH_SIZE+len("Ana") {
		t.Fatalf("unexpected serialized length: got %d want %d", len(data), protocol.TYPE_SIZE+protocol.LENGTH_SIZE+len("Ana"))
	}
	if data[0] != protocol.FieldTypeName.Byte() {
		t.Fatalf("wrong field type: got %d want %d", data[0], protocol.FieldTypeName.Byte())
	}
	if binary.BigEndian.Uint16(data[1:3]) != uint16(len("Ana")) {
		t.Fatalf("wrong length: got %d want %d", binary.BigEndian.Uint16(data[1:3]), len("Ana"))
	}
	if string(data[3:]) != "Ana" {
		t.Fatalf("wrong payload: got %q want %q", string(data[3:]), "Ana")
	}
}

func TestSerializeBetAddsFrameHeader(t *testing.T) {
	bet := &lottery.Bet{
		FirstName:     "Ana",
		LastName:      "Perez",
		Document:      12345678,
		BirthDate:     "1990-01-01",
		LotteryNumber: 7574,
		AgencyId:      "1",
	}

	payload := protocol.SerializeBet(bet)
	if len(payload) < protocol.TOTAL_LENGTH_SIZE {
		t.Fatalf("serialized bet too short: %d bytes", len(payload))
	}

	framedLength := binary.BigEndian.Uint32(payload[:protocol.TOTAL_LENGTH_SIZE])
	if uint32(len(payload)-protocol.TOTAL_LENGTH_SIZE) != framedLength {
		t.Fatalf("length prefix mismatch: got %d want %d", framedLength, len(payload)-protocol.TOTAL_LENGTH_SIZE)
	}
}

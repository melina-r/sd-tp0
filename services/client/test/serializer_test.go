package test

import (
	"encoding/binary"
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
)

func TestSerializeStringEncodesFieldTypeAndLength(t *testing.T) {
	data := SerializeString(FieldTypeName, "Ana")

	if len(data) != TYPE_SIZE+LENGTH_SIZE+len("Ana") {
		t.Fatalf("unexpected serialized length: got %d want %d", len(data), TYPE_SIZE+LENGTH_SIZE+len("Ana"))
	}
	if data[0] != FieldTypeName.Byte() {
		t.Fatalf("wrong field type: got %d want %d", data[0], FieldTypeName.Byte())
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

	payload := SerializeBet(bet)
	if len(payload) < TOTAL_LENGTH_SIZE {
		t.Fatalf("serialized bet too short: %d bytes", len(payload))
	}

	framedLength := binary.BigEndian.Uint32(payload[:TOTAL_LENGTH_SIZE])
	if uint32(len(payload)-TOTAL_LENGTH_SIZE) != framedLength {
		t.Fatalf("length prefix mismatch: got %d want %d", framedLength, len(payload)-TOTAL_LENGTH_SIZE)
	}
}

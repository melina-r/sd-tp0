package test

import (
	"testing"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
)

func TestDeserializeBetParsesAllFields(t *testing.T) {
	inputBet := &lottery.Bet{
		FirstName:     "Ana",
		LastName:      "Perez",
		Document:      12345678,
		BirthDate:     "1990-01-01",
		LotteryNumber: 7574,
		AgencyId:      "1",
	}

	serialized := SerializeBet(inputBet)
	decoded, endOfTransmission := DeserializeBet(serialized[TOTAL_LENGTH_SIZE:])
	if endOfTransmission {
		t.Fatal("expected a valid bet, got end-of-transmission")
	}
	if decoded == nil {
		t.Fatal("decoded bet should not be nil")
	}
	if decoded.FirstName != inputBet.FirstName || decoded.LastName != inputBet.LastName {
		t.Fatalf("unexpected names: got %s %s want %s %s", decoded.FirstName, decoded.LastName, inputBet.FirstName, inputBet.LastName)
	}
	if decoded.Document != inputBet.Document {
		t.Fatalf("unexpected document: got %d want %d", decoded.Document, inputBet.Document)
	}
	if decoded.BirthDate != inputBet.BirthDate {
		t.Fatalf("unexpected birth date: got %s want %s", decoded.BirthDate, inputBet.BirthDate)
	}
	if decoded.LotteryNumber != inputBet.LotteryNumber {
		t.Fatalf("unexpected lottery number: got %d want %d", decoded.LotteryNumber, inputBet.LotteryNumber)
	}
	if decoded.AgencyId != inputBet.AgencyId {
		t.Fatalf("unexpected agency id: got %s want %s", decoded.AgencyId, inputBet.AgencyId)
	}
}

func TestDeserializeBetRecognizesEndOfTransmission(t *testing.T) {
	serialized := SerializeEndOfTransmission()
	decoded, endOfTransmission := DeserializeBet(serialized[TOTAL_LENGTH_SIZE:])
	if !endOfTransmission {
		t.Fatal("expected end-of-transmission flag to be true")
	}
	if decoded == nil {
		t.Fatal("decoded bet should not be nil when EOT is detected")
	}
}

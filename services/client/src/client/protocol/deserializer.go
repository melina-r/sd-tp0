package protocol

import (
	"encoding/binary"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
)

func deserializeString(data []byte, length uint16) (string) {
	return string(data[:length])
}

func deserializeInt(data []byte) (int) {
	value := BytesToInt(data[:INT_SIZE])
	return value
}

func DeserializeBet(data []byte) (*lottery.Bet, bool) {
	bet := &lottery.Bet{}
	offset := uint32(0)

	for i := 0; i < 6; i++ {
		if offset >= uint32(len(data)) {
			return nil, false
		}

		fieldType := FieldType(data[offset])

		if fieldType == EndOfTransmission {
			return bet, true
		}
		offset++

		length := binary.BigEndian.Uint16(data[offset : offset+LENGTH_SIZE])
		offset += LENGTH_SIZE

		switch fieldType {
		case FieldTypeName:
			value := deserializeString(data[offset:], length)
			bet.FirstName = value
		case FieldTypeLastName:
			value := deserializeString(data[offset:], length)
			bet.LastName = value
		case FieldTypeBirthDate:
			value := deserializeString(data[offset:], length)
			bet.BirthDate = value
		case FieldTypeDocument:
			value := deserializeInt(data[offset:])
			bet.Document = int32(value)
		case FieldTypeLotteryNumber:
			value := deserializeInt(data[offset:])
			bet.LotteryNumber = int32(value)
		case FieldTypeAgencyId:
			value := deserializeString(data[offset:], length)
			bet.AgencyId = value
		default:
			return nil, false
		}

		offset += uint32(length)
	}

	return bet, false
}


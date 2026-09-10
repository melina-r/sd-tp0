package protocol

import (
	"encoding/binary"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
)

func deserializeString(data []byte, length uint16) string {
	return string(data[:length])
}

func deserializeInt(data []byte) int {
	value := BytesToInt(data[:INT_SIZE])
	return value
}

func DeserializeBet(data []byte) (*lottery.Bet, bool) {
	bet := &lottery.Bet{}
	offset := uint32(0)

	for offset < uint32(len(data)) {
		fieldType := FieldType(data[offset])
		if fieldType == EndOfTransmission {
			print("End of transmission reached - offset: ", offset, " total length: ", len(data), "\n")
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
			value := deserializeInt(data[offset:])
			bet.AgencyId = uint32(value)
		default:
			println("Error: unknown field type")
			return nil, false
		}

		offset += uint32(length)
	}

	return bet, false
}

func DeserializeBatch(data []byte) ([]lottery.Bet, bool) {
	bets := []lottery.Bet{}
	offset := uint32(0)

	for offset < uint32(len(data)) {
		if offset+TOTAL_LENGTH_SIZE > uint32(len(data)) {
			println("Error: not enough data to read bet length")
			break
		}

		betLength := binary.BigEndian.Uint32(data[offset : offset+TOTAL_LENGTH_SIZE])

		if betLength == 0 || offset+betLength > uint32(len(data)) {
			println("Error: invalid bet length or buffer overflow: ", betLength, "offset:", offset, "total length:", len(data))
			break
		}

		offset += TOTAL_LENGTH_SIZE
		betData := data[offset : offset+betLength]

		bet, eot := DeserializeBet(betData)
		if bet == nil {
			// TODO: Handle error case, maybe log it or return an error
			println("Error deserializing bet data")
			return nil, false
		}

		if eot {
			return bets, true
		}
		bets = append(bets, *bet)

		offset += betLength
	}

	return bets, false
}

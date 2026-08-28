package protocol

import "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"

func deserializeString(data []byte) (string, uint32) {
	if len(data) < 1 {
		return "", 0
	}

	length := uint32(data[0])
	if uint32(len(data)) < 1+length {
		return "", 0
	}

	return string(data[1 : 1+length]), 1 + length
}

func deserializeInt(data []byte) (int, uint32) {
	if len(data) < 4 {
		return 0, 0
	}

	value := bytesToInt(data[LENGTH_SIZE:INT_SIZE+LENGTH_SIZE])
	return value, INT_SIZE + LENGTH_SIZE
}

func DeserializeBet(data []byte) (*lottery.Bet, uint32) {
	bet := &lottery.Bet{}
	offset := uint32(0)

	for i := 0; i < 6; i++ {
		if offset >= uint32(len(data)) {
			return nil, 0
		}

		fieldType := FieldType(data[offset])
		offset++

		switch fieldType {
		case FieldTypeName:
			value, bytesRead := deserializeString(data[offset:])
			bet.FirstName = value
			offset += bytesRead
		case FieldTypeLastName:
			value, bytesRead := deserializeString(data[offset:])
			bet.LastName = value
			offset += bytesRead
		case FieldTypeBirthDate:
			value, bytesRead := deserializeString(data[offset:])
			bet.BirthDate = value
			offset += bytesRead
		case FieldTypeDocument:
			value, bytesRead := deserializeInt(data[offset:])
			bet.Document = int32(value)
			offset += bytesRead
		case FieldTypeLotteryNumber:
			value, bytesRead := deserializeInt(data[offset:])
			bet.LotteryNumber = int32(value)
			offset += bytesRead
		case FieldTypeAgencyId:
			value, bytesRead := deserializeInt(data[offset:])
			bet.AgencyId = int32(value)
			offset += bytesRead
		default:
			return nil, 0
		}
	}

	return bet, offset
}
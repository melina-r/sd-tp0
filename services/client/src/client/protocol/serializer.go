package protocol

import "github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"


func SerializeString(field FieldType, value string) []byte {
	bytes := []byte{field.byte()}
	bytes = append(bytes, byte(len(value)))
	return append(bytes, []byte(value)...)
}

func SerializeInt(field FieldType, value int) []byte {
	bytes := []byte{field.byte()}
	bytes = append(bytes, byte(INT_SIZE))
	return append(bytes, intToBytes(value)...)
}

func SerializeBet(bet *lottery.Bet) []byte {
	totalSize := bet.GetSerializedSize() + (TYPE_SIZE+LENGTH_SIZE)*FIELDS_COUNT
	serialized := make([]byte, 0, totalSize)

	serialized = append(serialized, SerializeString(FieldTypeName, bet.FirstName)...)
	serialized = append(serialized, SerializeString(FieldTypeLastName, bet.LastName)...)
	serialized = append(serialized, SerializeString(FieldTypeBirthDate, bet.BirthDate)...)
	serialized = append(serialized, SerializeInt(FieldTypeDocument, int(bet.Document))...)
	serialized = append(serialized, SerializeInt(FieldTypeLotteryNumber, int(bet.LotteryNumber))...)
	serialized = append(serialized, SerializeInt(FieldTypeAgencyId, int(bet.AgencyId))...)

	return serialized
}

package protocol

import (
	"encoding/binary"

	"github.com/7574-sistemas-distribuidos/tp-nivelador/src/client/lottery"
)

func SerializeString(field FieldType, value string) []byte {
	data := []byte(value)
	bytes := make([]byte, TYPE_SIZE+LENGTH_SIZE+len(data))
	bytes[0] = field.Byte()
	binary.BigEndian.PutUint16(bytes[TYPE_SIZE:], uint16(len(data)))
	copy(bytes[TYPE_SIZE+LENGTH_SIZE:], data)
	return bytes
}

func SerializeInt(field FieldType, value uint32) []byte {
	bytes := make([]byte, TYPE_SIZE+LENGTH_SIZE+INT_SIZE)
	bytes[0] = field.Byte()
	binary.BigEndian.PutUint16(bytes[TYPE_SIZE:], INT_SIZE)
	binary.BigEndian.PutUint32(bytes[TYPE_SIZE+LENGTH_SIZE:], value)
	return bytes
}

func SerializeBet(bet *lottery.Bet) []byte {
	var data []byte
	data = append(data, SerializeString(FieldTypeName, bet.FirstName)...)
	data = append(data, SerializeString(FieldTypeLastName, bet.LastName)...)
	data = append(data, SerializeInt(FieldTypeDocument, uint32(bet.Document))...)
	data = append(data, SerializeString(FieldTypeBirthDate, bet.BirthDate)...)
	data = append(data, SerializeInt(FieldTypeLotteryNumber, uint32(bet.LotteryNumber))...)
	data = append(data, SerializeInt(FieldTypeAgencyId, bet.AgencyId)...)

	totalLength := uint32(len(data))
	bytes := make([]byte, TOTAL_LENGTH_SIZE+totalLength)
	binary.BigEndian.PutUint32(bytes[:TOTAL_LENGTH_SIZE], totalLength)
	copy(bytes[TOTAL_LENGTH_SIZE:], data)

	return bytes
}

func SerializeEndOfTransmission(agencyId uint32) []byte {
	// Wrapped like a batch: BATCH_SIZE + AGENCY_ID + [TOTAL_LENGTH + END_OF_TRANSMISSION]
	
	eot_byte := EndOfTransmission.Byte()
	eot_length := TYPE_SIZE
	eot_data := make([]byte, TYPE_SIZE+TOTAL_LENGTH_SIZE)
	binary.BigEndian.PutUint32(eot_data[:TOTAL_LENGTH_SIZE], uint32(eot_length))
	eot_data[TOTAL_LENGTH_SIZE] = eot_byte

	total_length := uint32(len(eot_data)) + AGENCY_ID_SIZE
	eot_bytes := make([]byte, TOTAL_LENGTH_SIZE+total_length)
	binary.BigEndian.PutUint32(eot_bytes[:TOTAL_LENGTH_SIZE], total_length)
	binary.BigEndian.PutUint32(eot_bytes[TOTAL_LENGTH_SIZE:], agencyId)
	copy(eot_bytes[TOTAL_LENGTH_SIZE+AGENCY_ID_SIZE:], eot_data)
	
	return eot_bytes
}

func SerializeBatch(batch []byte, agencyId uint32) []byte {
	totalLength := uint32(len(batch)) + AGENCY_ID_SIZE
	bytes := make([]byte, TOTAL_LENGTH_SIZE+totalLength)
	binary.BigEndian.PutUint32(bytes, totalLength)
	binary.BigEndian.PutUint32(bytes[TOTAL_LENGTH_SIZE:], agencyId) 
	copy(bytes[TOTAL_LENGTH_SIZE+AGENCY_ID_SIZE:], batch)

	return bytes
}
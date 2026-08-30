package protocol

import "encoding/binary"

const (
	INT_SIZE          = 4
	TYPE_SIZE         = 1
	LENGTH_SIZE       = 2
	TOTAL_LENGTH_SIZE = 4
)

type FieldType uint8

const (
	EndOfTransmission FieldType = iota
	FieldTypeName
	FieldTypeLastName
	FieldTypeDocument
	FieldTypeBirthDate
	FieldTypeLotteryNumber
	FieldTypeAgencyId
)

func (f FieldType) Byte() byte {
	return byte(f)
}

func IntToBytes(n int) []byte {
	bytes_data := make([]byte, INT_SIZE)
	binary.BigEndian.PutUint32(bytes_data, uint32(n))
	return bytes_data
}

func BytesToInt(b []byte) int {
	return int(binary.BigEndian.Uint32(b))
}

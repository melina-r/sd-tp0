package protocol

const INT_SIZE = 4
const TYPE_SIZE = 1
const LENGTH_SIZE = 2
const FIELDS_COUNT = 6

type FieldType uint8
const (
	FieldTypeName FieldType = iota
	FieldTypeLastName
	FieldTypeDocument
	FieldTypeBirthDate
	FieldTypeLotteryNumber
	FieldTypeAgencyId
)
func (f FieldType) byte() byte {
	return byte(f)
}

func intToBytes(n int) []byte {
	return []byte{
		byte(n >> 24),
		byte(n >> 16),
		byte(n >> 8),
		byte(n),
	}
}

func bytesToInt(b []byte) int {
	return int(b[0])<<24 | int(b[1])<<16 | int(b[2])<<8 | int(b[3])
}

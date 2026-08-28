package lottery

const DOCUMENT_SIZE = 4
const AGENCY_ID_SIZE = 4
const LOTTERY_NUMBER_SIZE = 4

type Bet struct {
	FirstName  string	
	LastName string
	BirthDate string
	Document int32
	LotteryNumber int32
	AgencyId int32
}


func (b *Bet) GetSerializedSize() uint32 {
	return uint32(len(b.FirstName) + len(b.LastName) + len(b.BirthDate) + DOCUMENT_SIZE + LOTTERY_NUMBER_SIZE + AGENCY_ID_SIZE)
}
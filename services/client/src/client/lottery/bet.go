package lottery

import (
	"fmt"
	"strconv"
	"strings"
)

const DOCUMENT_SIZE = 4
const AGENCY_ID_SIZE = 4
const LOTTERY_NUMBER_SIZE = 4

type Bet struct {
	FirstName     string
	LastName      string
	BirthDate     string
	Document      int32
	LotteryNumber int32
	AgencyId      string
}

func (b *Bet) GetSerializedSize() uint32 {
	return uint32(len(b.FirstName) + len(b.LastName) + len(b.BirthDate) + DOCUMENT_SIZE + LOTTERY_NUMBER_SIZE + AGENCY_ID_SIZE)
}

func (b *Bet) FromCsvLine(csvLine string, agencyId string) error {
	fields := strings.Split(csvLine, ",")
	if len(fields) != 5 {
		return fmt.Errorf("invalid csv line: %q", csvLine)
	}

	document, err := strconv.ParseInt(strings.TrimSpace(fields[2]), 10, 32)
	if err != nil {
		return fmt.Errorf("invalid document: %q: %w", fields[2], err)
	}

	lotteryNumber, err := strconv.ParseInt(strings.TrimSpace(fields[4]), 10, 32)
	if err != nil {
		return fmt.Errorf("invalid lottery number: %q: %w", fields[4], err)
	}

	b.FirstName = strings.TrimSpace(fields[0])
	b.LastName = strings.TrimSpace(fields[1])
	b.Document = int32(document)
	b.BirthDate = strings.TrimSpace(fields[3])
	b.LotteryNumber = int32(lotteryNumber)
	b.AgencyId = agencyId

	return nil
}

func (b *Bet) ToCsvLine() string {
	return fmt.Sprintf("%s,%s,%d,%s,%d", b.FirstName, b.LastName, b.Document, b.BirthDate, b.LotteryNumber)
}

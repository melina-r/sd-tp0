from protocol.utils import (
    END_OF_TRANSMISSION,
    FIELD_TYPE_NAME,
    FIELD_TYPE_LAST_NAME,
    FIELD_TYPE_DOCUMENT,
    FIELD_TYPE_BIRTH_DATE,
    FIELD_TYPE_LOTTERY_NUMBER,
    FIELD_TYPE_AGENCY_ID,
    TOTAL_LENGTH_SIZE,
    TYPE_SIZE,
    LENGTH_SIZE,
    INT_SIZE,
)
from lottery import Bet

def deserialize_int(data: bytes) -> int:
    """Returns the integer value from the given bytes."""
    return int.from_bytes(data[:INT_SIZE], byteorder="big")

def deserialize_string(data: bytes, length: int) -> str:
    """Returns the string value from the given bytes."""
    return data[:length].decode("utf-8")

def deserialize_bet(data: bytes) -> Bet:
    """Deserializes a Bet object from the given bytes. 
    If the FieldType is END_OF_TRANSMISSION, it returns None."""
    bet = {}
    offset = 0

    while offset < len(data):
        field_type = data[offset]
        if field_type == END_OF_TRANSMISSION:
            print("End of transmission reached while deserializing bet.")
            return None

        field_length = int.from_bytes(data[offset + TYPE_SIZE:offset + TYPE_SIZE + LENGTH_SIZE], byteorder="big")
        offset += TYPE_SIZE + LENGTH_SIZE

        if field_type == FIELD_TYPE_NAME:
            bet["first_name"] = deserialize_string(data[offset:], field_length)
        elif field_type == FIELD_TYPE_LAST_NAME:
            bet["last_name"] = deserialize_string(data[offset:], field_length)
        elif field_type == FIELD_TYPE_DOCUMENT:
            bet["document"] = deserialize_int(data[offset:])
        elif field_type == FIELD_TYPE_BIRTH_DATE:
            bet["birthdate"] = deserialize_string(data[offset:], field_length)
        elif field_type == FIELD_TYPE_LOTTERY_NUMBER:
            bet["number"] = deserialize_int(data[offset:])
        elif field_type == FIELD_TYPE_AGENCY_ID:
            bet["agency_id"] = deserialize_int(data[offset:])

        offset += field_length

    agency_id = bet.get("agency_id")
    if agency_id is not None:
        agency_id = int(agency_id)

    return Bet(
        agency_id=agency_id,
        first_name=bet.get("first_name"),
        last_name=bet.get("last_name"),
        document=bet.get("document"),
        birthdate=bet.get("birthdate"),
        number=bet.get("number"),
    )

def deserialize_batch(data: bytes) -> (list[Bet], bool):
    """Deserializes a batch of Bet objects from the given bytes. 
    Returns a tuple containing the list of bets and a boolean indicating
    if End of Transmission was reached during deserialization."""
    bets = []
    offset = 0

    while offset < len(data):
        total_length = int.from_bytes(data[offset:offset + TOTAL_LENGTH_SIZE], byteorder="big")
        offset += TOTAL_LENGTH_SIZE

        bet_data = data[offset:offset + total_length]
        bet = deserialize_bet(bet_data)
        if bet is not None:
            bets.append(bet)
        else:
            return bets, True

        offset += total_length

    return bets, False

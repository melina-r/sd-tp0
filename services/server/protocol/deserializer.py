from protocol.utils import (
    END_OF_TRANSMISSION,
    FIELD_TYPE_NAME,
    FIELD_TYPE_LAST_NAME,
    FIELD_TYPE_DOCUMENT,
    FIELD_TYPE_BIRTH_DATE,
    FIELD_TYPE_LOTTERY_NUMBER,
    FIELD_TYPE_AGENCY_ID,
    TYPE_SIZE,
    LENGTH_SIZE,
    INT_SIZE,
)
from lottery import Bet

def deserialize_int(data: bytes) -> int:
    return int.from_bytes(data[:INT_SIZE], byteorder="big")

def deserialize_string(data: bytes, length: int) -> str:
    return data[:length].decode("utf-8")

def deserialize_bet(data: bytes) -> Bet:
    bet = {}
    offset = 0

    while offset < len(data):
        field_type = data[offset]
        if field_type == END_OF_TRANSMISSION:
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
            bet["agency_id"] = deserialize_string(data[offset:], field_length)

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

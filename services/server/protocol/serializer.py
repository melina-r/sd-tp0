from lottery import Bet
from protocol.utils import (
    get_serialized_size,
    int_to_bytes,
    END_OF_TRANSMISSION,
    FIELD_TYPE_NAME,
    FIELD_TYPE_LAST_NAME,
    FIELD_TYPE_DOCUMENT,
    FIELD_TYPE_BIRTH_DATE,
    FIELD_TYPE_LOTTERY_NUMBER,
    FIELD_TYPE_AGENCY_ID,
    TYPE_SIZE,
    LENGTH_SIZE,
    FIELDS_COUNT,
    INT_SIZE,
    TOTAL_LENGTH_SIZE,
)

def serialize_int(field: int, value: int) -> bytes:
    bytes_data = field.to_bytes(TYPE_SIZE, byteorder="big") + INT_SIZE.to_bytes(LENGTH_SIZE, byteorder="big") + int_to_bytes(value, INT_SIZE)
    return bytes_data

def serialize_string(field: int, value: str) -> bytes:
    encoded_value = value.encode("utf-8")
    bytes_data = field.to_bytes(TYPE_SIZE, byteorder="big") + len(encoded_value).to_bytes(LENGTH_SIZE, byteorder="big")
    bytes_data += encoded_value
    return bytes_data

def serialize_bet(bet: Bet) -> bytes:
    serialized_data = b""

    total_size = get_serialized_size(bet) + (TYPE_SIZE + LENGTH_SIZE) * FIELDS_COUNT
    serialized_data += total_size.to_bytes(TOTAL_LENGTH_SIZE, byteorder="big")

    serialized_data += serialize_string(FIELD_TYPE_NAME, bet.first_name)

    serialized_data += serialize_string(FIELD_TYPE_LAST_NAME, bet.last_name)

    serialized_data += serialize_int(FIELD_TYPE_DOCUMENT, bet.document)

    serialized_data += serialize_string(FIELD_TYPE_BIRTH_DATE, bet.birthdate)

    serialized_data += serialize_int(FIELD_TYPE_LOTTERY_NUMBER, bet.number)

    serialized_data += serialize_int(FIELD_TYPE_AGENCY_ID, bet.agency_id)
    return serialized_data

def serialize_end_of_transmission() -> bytes:
    bytes_data = END_OF_TRANSMISSION.to_bytes(TYPE_SIZE, byteorder="big") + (0).to_bytes(LENGTH_SIZE, byteorder="big")
    total_length = len(bytes_data)
    return total_length.to_bytes(TOTAL_LENGTH_SIZE, byteorder="big") + bytes_data

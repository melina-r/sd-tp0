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
    """Serializes an integer value into bytes with the given field type and sets the length to INT_SIZE."""
    bytes_data = field.to_bytes(TYPE_SIZE, byteorder="big") + INT_SIZE.to_bytes(LENGTH_SIZE, byteorder="big") + int_to_bytes(value, INT_SIZE)
    return bytes_data

def serialize_string(field: int, value: str) -> bytes:
    """Serializes a string value into bytes with the given field type 
    and sets the length to the length of the encoded string."""
    encoded_value = value.encode("utf-8")
    bytes_data = field.to_bytes(TYPE_SIZE, byteorder="big") + len(encoded_value).to_bytes(LENGTH_SIZE, byteorder="big")
    bytes_data += encoded_value
    if bytes_data[0] != field:
        print(f"Error: Expected field type {field}, but got {bytes_data[0]}")
    return bytes_data

def serialize_bet(bet: Bet) -> bytes:
    """Serializes a Bet object into bytes, including all its fields
    and their respective lengths. The total size of the serialized 
    data is prepended to the byte stream."""
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

def serialize_batch(bets: list[Bet]) -> bytes:
    """Serializes a list of Bet objects into bytes, including the total size of the serialized data."""
    serialized_data = b""
    for bet in bets:
        serialized_data += serialize_bet(bet)
    total_size = len(serialized_data)
    bytes_data = total_size.to_bytes(TOTAL_LENGTH_SIZE, byteorder="big") + serialized_data
    return bytes_data

def serialize_end_of_transmission() -> bytes:
    """Serializes an End of Transmission signal into bytes, 
    including the total size of the serialized data."""
    bytes_data = END_OF_TRANSMISSION.to_bytes(TYPE_SIZE, byteorder="big") + (0).to_bytes(LENGTH_SIZE, byteorder="big")
    total_length = len(bytes_data)
    return total_length.to_bytes(TOTAL_LENGTH_SIZE, byteorder="big") + bytes_data

def serialize_acknowledgment() -> bytes:
    """Serializes an acknowledgment signal into bytes."""
    ack = b"1"
    return ack
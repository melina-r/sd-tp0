from lottery import Bet

INT_SIZE = 4
TYPE_SIZE = 1
LENGTH_SIZE = 2
TOTAL_LENGTH_SIZE = 4
FIELDS_COUNT = 6

# Tipos de campo (Type)
END_OF_TRANSMISSION = 0
FIELD_TYPE_NAME = 1
FIELD_TYPE_LAST_NAME = 2
FIELD_TYPE_DOCUMENT = 3
FIELD_TYPE_BIRTH_DATE = 4
FIELD_TYPE_LOTTERY_NUMBER = 5
FIELD_TYPE_AGENCY_ID = 6

DOCUMENT_SIZE = 4
LOTTERY_NUMBER_SIZE = 4


def int_to_bytes(value: int, length: int) -> bytes:
    return value.to_bytes(length, byteorder="big")

def bytes_to_int(value: bytes) -> int:
    return int.from_bytes(value, byteorder="big")

def get_serialized_size(bet: Bet) -> int:
    agency_id_bytes = str(bet.agency_id).encode("utf-8")
    size = (
        len(bet.first_name.encode("utf-8"))
        + len(bet.last_name.encode("utf-8"))
        + len(bet.birthdate.encode("utf-8"))
        + DOCUMENT_SIZE
        + LOTTERY_NUMBER_SIZE
        + len(agency_id_bytes)
    )
    return size

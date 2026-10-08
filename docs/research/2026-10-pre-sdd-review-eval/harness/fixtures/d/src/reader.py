from src.contract import RECORD_KEYS

def read_record(record):
    if set(record) != RECORD_KEYS:
        raise ValueError("Invalid record shape")
    return record["sequence"], record["payload"]

from src.writer import event_record
from src.reader import read_record

def roundtrip(sequence, payload):
    return read_record(event_record(sequence, payload))

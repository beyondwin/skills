# Approved event-origin implementation plan
**Spec:** design.md
Status: Approved. Implementation has not started. Base: current HEAD.

## Task 1: Add origin
Modify: `src/writer.py`.
Add `"origin": "local"` to the record produced by `event_record(sequence, payload)`.
Keep its signature and the other two values unchanged.
The remaining source modules need no edit because `src/reader.py` reads just
sequence and payload and still returns a two-tuple.

## Task 2: Behavioral acceptance
Create: `tests/contracts/test_origin.py`.
Use unittest with class `OriginTest` and methods starting `test_`.
Assert exact output keys and origin, a direct writer-reader roundtrip, and
ValueError on missing origin or an extra key. Assert a padded mixed-case payload
is returned unchanged. Keep the existing pipeline regression.
Do not add or alter other files.

## Task 3: Verification
Run `python3 -m unittest discover -s tests -p "test_*.py" -v` from repository root.
Require exit 0; this discovers and runs all the new contract tests in Task 2
as well as the existing pipeline regression.

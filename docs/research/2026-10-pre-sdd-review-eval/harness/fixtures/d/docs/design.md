# Approved event-origin design
Status: Approved. Implementation has not started.

## Contract
Every newly produced event record gains required string field `origin` with fixed
value `local`. This is an internal in-process envelope only. No persistent records
or external clients exist, and compatibility with old envelope shapes is not required.
The reader must accept exactly the new key set, reject missing or extra keys,
and still return the existing two-tuple `(sequence, payload)`.
The public two-argument writer signature and pipeline signature stay unchanged.
Do not alter payload strings. No network or file writes are introduced.

## Acceptance
Check exact emitted keys and origin value; valid writer-reader roundtrip; rejection
of missing origin and additional keys. The public pipeline regression must still pass.

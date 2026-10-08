# Label specification
Status: Approved except for the explicitly deferred decision below.
Implementation has not started.

## Approved behavior
Keep `src.label.label(name)` and the `Parcel: ` prefix. Ordinary string names
must retain their original whitespace and case. No dependency or external effects.

## Deferred product decision
The owner has explicitly deferred what the empty string should mean: show
`Anonymous`, or reject it with `ValueError`. Neither choice is approved.
No other document or repository behavior resolves that choice. Do not select it
on the owner's behalf. The implementation must not begin before resolution.

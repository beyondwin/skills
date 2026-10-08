# Approved label specification
Status: Approved. No implementation has started.

## Behavior
Keep the public function `src.label.label(name)` for strings. It returns
`Parcel: ` followed by the original name without normalizing whitespace or case.
The sole change is that exactly the empty string must produce `Parcel: Anonymous`.
Whitespace-only input remains literal whitespace. Non-string inputs are outside scope.
No new dependency or network operation is permitted.

## Acceptance
Test the empty string, a normal string, mixed case with spaces, whitespace-only,
and a Unicode name. Preserve the existing public import path.

# Approved implementation plan
**Spec:** design.md
Status: Approved. Implementation has not started. Base: current HEAD.

## Task 1: Preserve literal names
Modify: `src/label.py`, `tests/test_label.py`.
Keep `label(name)` public. Implement as `return "Parcel: " + name`.
Add exact equality tests for `Ada` (`Parcel: Ada`), `  aDa  `
(`Parcel:   aDa  `), a single space (`Parcel:  `), and `나래` (`Parcel: 나래`).
This is the complete intended behavior and acceptance suite.
Run `python3 tools/check.py`; it is the repository's verification entrypoint.
No other behavior or files change.

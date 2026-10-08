# Approved implementation plan
**Spec:** design.md
Status: Approved. Implementation has not started. Base: current HEAD.

## Task 1: Empty-label fallback
Modify: `src/label.py`, `tests/test_label.py`.
Keep `label(name)` public; if `name == ""`, use `Anonymous`; otherwise use the
input string unchanged. Prefix the chosen string with `Parcel: `.
Add separate exact equality tests for empty string (`Parcel: Anonymous`),
`Ada` (`Parcel: Ada`), `  aDa  ` (`Parcel:   aDa  `), a single space
(`Parcel:  `), and `나래` (`Parcel: 나래`). Keep the existing regression.
Run `python3 -m unittest discover -s tests -p "test_*.py" -v` and verify
these named new tests execute and pass. No other behavior or files change.

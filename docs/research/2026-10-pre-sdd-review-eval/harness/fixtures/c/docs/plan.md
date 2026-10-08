# Label implementation plan
**Spec:** design.md
Status: Approved except for the product decision referenced by Task 1.
Implementation has not started. Base: current HEAD.

## Task 1: Empty-label handling
Modify: `src/label.py`, `tests/test_label.py`.
Keep ordinary strings literal. For empty string use the behavior that the
owner selects in the linked design. Add one exact test for that behavior,
plus exact tests for normal, mixed-case padded, whitespace-only, and Unicode names.
Run `python3 -m unittest discover -s tests -p "test_*.py" -v`, checking that
the new tests are listed and pass. Do not make unrelated changes.

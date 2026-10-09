# Finding representation correction

The frozen rubric requires JSON containing finding arrays but does not explicitly
require each finding to be a string. One completed Opus judgment used objects
with `phrase` and `issue` strings. The original parser rejected that shape even
though the preference, labels and finding content were unambiguous. Treating it
as a missing preference would measure a parser mismatch rather than the judgment.

`score.py` leaves all frozen files and raw responses unchanged. It accepts a finding
as a string or a nonempty object of string fields, applies that rule to every
judgment, and retains the exact preference. It still rejects unknown labels,
missing required fields, non-list finding collections and nested/nontext findings.
No judgment is retried and no wording or vote is rewritten. Finding counts remain
array lengths. Scorer tests cover both shapes, invalid labels, missing votes and
order disagreement. This is a declared post-freeze scorer repair, not a change to
the adoption threshold or a human adjudication replacing model votes.

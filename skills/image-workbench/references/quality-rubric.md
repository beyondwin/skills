# Image Quality Rubric

## Status Semantics

Use exactly four evidence statuses:

- `verified`: directly observed in the current run.
- `partially_verified`: a stated subset was observed and the missing portion is named.
- `not_measured`: no current evidence was collected.
- `blocked`: a required check could not run and its blocker is named.

## Visual Criteria

Open each deliverable candidate and check content completeness;
composition/crop; style, palette, material, and light; stated invariants; exact
visible copy or marks; and visible artifacts. Visual review remains required
even when file facts are available.

Use the original condition's referent and strength, not a stricter or weaker
summary. For an exact count, first locate each directly visible instance once
(for example, left rear, left front, right rear, right front), then compare the
observed total with the requested total. Do not count a shadow or infer a hidden
part from symmetry. A partly overlapping part can still be directly identifiable.
If a small part is unclear, make one detail check that keeps its surrounding
context. If it remains unclear, mark it unverified instead of repeatedly cropping
or treating uncertainty as proof that the part is missing.

Check the kind of visibility actually requested:

- Whole-subject framing: the subject fits inside the frame with the requested margin.
- Visible named parts: each part is directly identifiable, including any expressly
  required endpoint or ground contact. Partial overlap alone does not fail this check.
- Explicitly fully visible or unobstructed objects: trace each required outline and
  extremity; another object, a container rim, or the frame must not cut it off.
  A correct count does not establish this stronger condition.

Before a complete-visibility pass, briefly name each target's lowest visible edge
or endpoint and the foreground surface beside it. Check where those boundaries
meet: if the foreground surface supplies the visible boundary instead of the
target's own contour, it is occluded. "Countable" and "inside the frame" do not
answer this check. Use one focused look at that junction, not another general review.

Do not apply a whole subject's framing qualifier to every component's silhouette.
Before rejecting, connect the original condition to a visible contradiction and
its location. If a critical detail remains unclear, report it as unverified;
uncertainty is neither proof of a defect nor a pass. Keep aesthetic preferences
advisory unless the original request makes them critical.

## Mechanical Criteria

For a project-bound final file, record detected format, dimensions, alpha when
exposed, byte size, SHA-256, extension match, and trailing bytes with the local
inspector, and confirm the destination path separately. These facts describe
the file; they do not judge aesthetics, rights, or the result of an edit.

The inspector verifies selected file facts and required parsed structure,
not complete bitstream decoding. Visual quality and rights remain separate
checks. Its JSON output must not alias the input asset; an existing
`--output` target must be a JSON report, never an image or other file.

## Critical Versus Advisory

Critical failures include a missing subject, failed edit invariant, incorrect
exact copy, unsafe crop, unverifiable path or dimensions for project handoff,
unauthorized overwrite, and an unknown material rights or privacy boundary.
An aesthetic preference is advisory unless the request makes it
acceptance-critical.

## Exact Copy And Invariants

Treat literal text, protected marks, identity, preserved background, crop-safe
area, and required layout as explicit checks. If an exact requirement cannot be
directly inspected or constructed deterministically, hold the handoff instead
of inferring success.

## Sufficient Evidence

Use the stopping rule in `SKILL.md` under Inspect And Evaluate: distinguish a
visible failure from a condition that still needs measurement. A failed
critical condition rejects the candidate even when file checks pass. Report
what was observed and what remains unverified; the evidence statuses do not
turn a rejected candidate into an accepted one.

## Targeted Iteration

Name one failed critical or acceptance condition, apply one justified correction,
preserving the complete original drawing brief, then reopen the candidate and repeat every original critical check, including previously passing ones. Stop when
the acceptance conditions are satisfied or a material condition remains blocked.

## Final Handoff

Report the path or preview, final prompt, operation or route, and all critical
statuses. Include whether integration changed consuming code or metadata. No
automatic score can replace opening the candidate.

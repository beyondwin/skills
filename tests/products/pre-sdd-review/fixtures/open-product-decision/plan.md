# sample-app message rendering plan

**Spec:** design.md

## Implementation

1. Create `renderMessage(input: string): string` in `src/app.ts`. Make it
   throw `Error("empty input")` when `input` is `""`, and otherwise return
   `input`.
2. Add a unit test in `tests/app.test.ts` that calls
   `renderMessage("  Mixed Case, 42!  ")` and verifies that it returns
   `"  Mixed Case, 42!  "` with the spaces and case kept.
3. Add a unit test in `tests/app.test.ts` that verifies `renderMessage("")`
   throws `Error("empty input")`.
4. Run `npm test` and `npm run build`.

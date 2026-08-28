# sample-app message rendering plan

**Spec:** design.md

## Implementation

1. Create `renderMessage(input: string): string` in `src/app.ts`.
2. Add a unit test in `tests/app.test.ts` that calls `renderMessage("hello")`
   and verifies that it returns `"hello"`.
3. Add a unit test in `tests/app.test.ts` that calls `renderMessage("bye")`
   and verifies that it returns `"bye"`.
4. Run `npm test` and `npm run build`.

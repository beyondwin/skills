# sample-app review queue plan

**Spec:** design.md

## Implementation

1. Store queue entries as `researching`, `approved`, or `hold` in `src/app.ts`.
2. In `tests/app.test.ts`, verify registry parity for every `approved` entry.
3. Run `npm test` and `npm run build`.

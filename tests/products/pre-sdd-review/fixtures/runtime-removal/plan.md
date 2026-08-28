# sample-app runtime replacement plan

**Spec:** design.md

## Implementation

1. Remove `src/app.ts`.
2. Replace the application runtime and move message rendering to the new runtime.
3. Run `npm test` and `npm run build`.

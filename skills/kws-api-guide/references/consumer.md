# To-do section for the calling side

Write this section only when the user gave a consumer repository.

## Gather

- Fetch the consumer's default branch and record its commit. Say which branch on the page and
  in the report.
- Find every call to the endpoints in scope: search for the base paths, path fragments, and
  distinctive field names.
- For each call, compare what the consumer sends and expects with the facts on the cards:
  removed or renamed fields, enum sets the consumer rejects when a new value arrives, null
  handling, size limits copied into the client, local calculations that duplicate a server
  value, and temporary or fake behavior standing in for an endpoint that now exists.

## Write

- One table: tag, what to do, link to the card.
- Rows that break the current consumer come first, tagged first. Then new wiring, then
  removing stand-ins and cleanup.
- Each row says what changed on the server and what the caller should do, in behavior terms.
  Do not put consumer file paths, line numbers, or class names on the page; the user may want
  them in the chat report instead.
- Do not prescribe the consumer's architecture, state management, or library choices.
- A short lede above the table says what is already wired and what is not.

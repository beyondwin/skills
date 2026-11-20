# Collecting facts from code

Read at the recorded commit. For each item, note the file and line you read; the Verify step
and the report use them.

## Find the endpoints

- Start from the scope. For a diff, list changed controllers, routes, DTOs, contract files,
  and error code enums: `git diff --stat base..head`.
- Map each route to the full path the caller uses. Check the gateway or proxy prefix and the
  service's own base path; they are often in different files.
- Group cards by the base path the caller configures, since that is what the caller sets up.

## Per endpoint

| Item | Where to look | Write down |
| --- | --- | --- |
| Auth | security filter, role checks in the handler or service | who may call it and the code each refusal returns |
| Request | path and query parameters, body DTO, validation annotations, manual checks in the service | type, required or not, default, what an empty value does, rejected extra or repeated parameters, body size limit, content type |
| Response | response DTO, the code that builds it, serializer settings | each field's type, whether it can be null, whether a null key is sent or left out, full enum sets, list order and length, date format and time zone |
| Status | handler return values | which 2xx codes, and whether the body shape differs between them |
| Errors | throw sites reachable from the handler, the global exception handler, framework errors (type mismatch, unsupported media type, method not allowed) | HTTP status, code, the condition in caller terms |
| Headers | handler, filters, response wrappers | `Retry-After` and its value, cache headers, `Location`, any custom header; per endpoint, not per service |
| Limits | configuration properties and their defaults | the default, the property name, whether deployed values were checked |
| Repeats | idempotency keys, dedupe, locks | what a repeated or concurrent request returns |

## Fields that depend on state

When which fields are present depends on a status, build the table from the code that fills
the response for each status, not from the field comments. Check every status, including
ones that only appear briefly while work is in progress.

## Multi-step flows

For an upload, a job, or anything the caller polls:

- List every state, what moves the item from one state to the next, which states are final,
  and the time limits on each.
- For each step, say what the server can observe and what it cannot. A presigned upload goes
  straight to storage; the server learns it finished only when the caller says so or when it
  checks storage.
- Say what the caller should do for each state it can see, and what to do when a response
  never arrives.
- Branch on the status in the body when the HTTP code alone does not tell the states apart.

## Common rules

Check these once for the whole page, then verify each against every service in scope:

- The response envelope for success and failure, and which field to branch on.
- Which proxy or gateway errors arrive without the envelope.
- Authentication header, and the one request that does not carry it (such as a storage PUT).
- ID format (say not to assume one), date and date-time formats, time zone.

## Examples

- Prefer responses captured from a running local server with test data. Replace anything that
  looks like a real person, token, key, or internal host.
- Without a running server, compose the example from the response type and label it composed.
- Keep long arrays short with a visible `...`.

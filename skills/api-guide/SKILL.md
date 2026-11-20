---
name: api-guide
description: Use when explicitly invoked and the user wants a shareable guide that tells web, app, or server developers how to call APIs that were added or changed, checked against the server code and published as a Claude artifact. Do not use for writing or fixing OpenAPI files, generating a reference site from a spec, code review, implementing the client, or explaining how one mechanism works (how-it-works).
disable-model-invocation: true
license: Apache-2.0
compatibility: Requires Claude Code with the Artifact tool and read access to the server source.
metadata:
  version: "1.0.0"
  updated_at: "2026-11-20"
---

# api-guide

Activate only on explicit invocation: `/api-guide`. Matching task text alone does not activate it.

The result is one page, published as a Claude artifact, that lets a developer on another team
call the APIs without reading the server code. Server facts on the page must be exact. Advice
about the calling side stays at the level of behavior.

## Inputs

Fill these before writing. If one is missing and would change the page, ask one question for
the first such slot; otherwise use the default and say which default you used.

| Slot | Default |
| --- | --- |
| scope: endpoints, a feature, or a diff `base..head` | the current branch against its merge base with the default branch |
| reader: web, app, or server developers | ask; it sets the type notation (TypeScript, Dart, Kotlin, Swift, or Java) |
| consumer repository (optional) | none; without it the page has no to-do section |
| existing artifact URL (optional) | none; with it, read the page and update the same URL |
| language | the user's language |

## Steps

1. Pin the sources. Fetch, record the server commit (and the consumer commit, from the
   consumer's latest default branch), and read files at those commits, not a dirty tree.
2. Collect facts from code for every endpoint in scope. Read `references/facts.md`.
   A contract file (OpenAPI, protobuf) is a map of where to look, not the answer.
3. Tag each endpoint and field new, changed, or unchanged from the diff against the base,
   not from memory. A removed field goes on the changed card with what replaced it.
4. Only with a consumer repository: read `references/consumer.md` and write the to-do section.
5. Write the page from `references/page.html`. Keep its components and section order. Follow
   the host's artifact design skill for the page contract; for a flow diagram, its
   diagramming skill.
6. Run the checks in Verify. Fix the page, then check again.
7. Publish with the Artifact tool. A revision publishes the same file to the same URL. The page
   is private; tell the user it is shared from the page's Share menu.
8. Report, per Report.

## Page skeleton

Fixed order. Leave out a section only where marked optional.

1. Header: title of two to four words, one lede paragraph (what the page covers, that every
   card has the same order, whether examples were captured or composed), and chips for each
   base path and for `as of {date}, server {short sha}`.
2. To-do (optional, needs a consumer repository).
3. Common rules: authentication, the response envelope and what to branch on, which 2xx codes
   mean success, type notation and nullability, ID and date formats with time zone, unknown
   enum values, headers (which endpoints send `Retry-After`, cache headers), errors any
   endpoint can return, and bodies that are not the envelope (a proxy's 502 or 504).
4. API cards, grouped by service or base path. Every card in this order: head (method, full
   path, new or changed tag), when to call it, Request, Response (type, field table, a table
   of which fields come with which status when that varies, an example in a collapsed block),
   Errors (HTTP, code, when, what the caller does), Handling (numbered steps).
5. Flows (optional): a multi-step operation such as an upload, a job, or polling, with a
   diagram and a table keyed by the status the caller sees.
6. Shared caller rules (optional): rules several cards rely on, such as drawing a list row.
7. Appendix (optional): client models in the reader's language, and the server files the
   page was checked against.

## Verify

Before publishing, every item holds:

- Every path, field, enum value, code, header, and limit has a code location you read at the
  recorded commit.
- Before writing all, every, only, never, or same as, search for a counterexample.
- A field name used in two responses follows the same rule in both, or each card defines it.
- Appendix models and examples agree with the field tables on names and nullability.
- Each card's error table covers the throw sites reachable from that handler, request
  validation, the auth layer, and body size limits.
- A limit read from configuration names its default; deployed values are checked or the page
  says they were not.
- An example is called captured only if a running server returned it; otherwise it is labeled
  composed from the response type. No real personal data, tokens, or keys appear.
- For a large scope, split fact checks across subagents by service, and reopen every finding
  that would change the page before you use it.

## Report

In the user's language, briefly: the link, what was checked and at which commits, what was not
checked (deployed values, live calls), gaps found in contract files (report them; do not fix
them unless asked), and one next step.

## Gotchas

From checking a hand-written guide of this kind against its server code before this skill
existed (12 endpoints in two services, 2026-11). No run of the skill itself is recorded yet.

- The OpenAPI file listed fewer error codes than the handlers threw, and the guide also
  missed codes the handlers threw (a body size limit, a rejected extra query parameter).
  Read the throw sites.
- Two claims about every endpoint were false: a cache header that only one of the two services
  set, and which endpoints return 429 with `Retry-After`.
- A card said its errors were the same as another endpoint's; the second endpoint rejected a
  range of years the first accepted.
- A boolean with the same name meant different things in two responses: one counted an item
  still being processed, the other did not.
- The appendix model declared fields non-null that the field table allowed to be null.
- The to-do column listed consumer file paths and line numbers. The user wanted less consumer
  code detail and exact server facts instead.
- The page told callers to request a fresh upload URL after a timeout, which made a caller that
  had already finished the upload send the whole file again. The server could not see whether
  the upload had finished. Say what the server can and cannot observe at each step.

# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

The current standalone products are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md), and [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md). How It Works currently claims Codex and Claude Code. The other three products keep their registered Codex boundaries.

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

## Contract portability versus measured support

A matching folder layout does not mean that host is supported. A host is `supported` only after a current smoke test. Otherwise its status is `partially verified` or `not_measured`. See each product README for the product guide.

`how-it-works` supports Codex and Claude Code for local or repository-based use. Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

`image-workbench` is Codex-only. Similar tools in another host do not establish compatibility.

Other hosts for `pre-sdd-review` remain `not_measured`.

The catalog plugin name is `beyondwin-skills`. That does not mean a marketplace listing.

## Install paths and hosts

Install, link, and remove steps are in [Installation](installation.md). Verification is in [Verification](verification.md).

Windows-meaningful checks are the Korean-editor offline suite and repository contracts. Do not claim `image-workbench` generate or edit support except where Codex is present.

The license is Apache-2.0.

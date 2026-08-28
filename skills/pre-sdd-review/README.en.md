# Pre-SDD Review

[한국어](README.md)

## Purpose

It reviews an approved design and implementation plan against repository reality immediately before SDD, repairs the documents within authorization, and reviews them again. The skill never starts SDD itself.

## When to use and not use

The default is review-repair-re-review. `review-only` is explicit. Do not use it to create specs or plans, review code, implement changes, proofread, or assess release readiness.

## Supported hosts

pre-sdd-review: Codex is the only measured host. Other hosts are not measured.

## Install

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

Shared installation guidance is in [Installation](../../docs/users/en/installation.md).

## First call

```text
$pre-sdd-review docs/design.md docs/plan.md
```

## Expected result

The result reports the review, any authorized document repair, and the re-review state. It does not start SDD.

## Safety and privacy

Respect the boundaries of the repository and readable documents. Do not store private material in fixtures or logs.

## Verification

Codex is the only measured host; product contract verification is deterministic offline evidence.

## Update and remove

Before updating or removing, inspect the exact installation target and the name and version in `SKILL.md`.

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](../../docs/maintainers/products/pre-sdd-review/release.md)

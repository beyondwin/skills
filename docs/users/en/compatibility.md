# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

The current standalone products are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md), and [`sddx`](../../../skills/sddx/README.en.md). How It Works and SDDx currently claim Codex and Claude Code. Korean Writing Editor and Pre-SDD Review keep their registered Codex boundaries. Image Workbench claims Codex and Grok.

In short: the Korean editor and Pre-SDD Review are confirmed on Codex today. Image Workbench is confirmed on Codex and Grok. How It Works and SDDx link this repo for Codex and Claude Code.

A host is the program that runs the skill. A smoke is a recorded live run. `not_measured` means not checked yet. `historical-unbound` is an old record. `current-bounded` means only version and hash are bound.

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

sddx: Claude Code and Codex supported for local or repository-based use.

## Contract portability versus measured support

A matching folder layout does not mean that host is supported. Adding a new supported host requires smoke evidence from the current build and an explicit support decision. Established support scope and current measurement status are separate. Record unmeasured current execution as `not_measured`; that alone does not change the established support scope. See each product README for the product guide.

`how-it-works` supports Codex and Claude Code for local or repository-based use. Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

`image-workbench` can make or edit an image only when this host has its own image tool and you can open the result. The Grok shortcut is `~/.agents/skills/image-workbench`. A similar tool on another host is not support.

Other hosts for `pre-sdd-review` remain `not_measured`.

The preserved `how-it-works` smoke is `historical-unbound`; it is separate from current payload and model execution evidence. Actual execution of the current install files is `not_measured`. `current-bounded` validates version/hash and metadata binding only, not actual execution or explanation quality. No new native Windows measurement was made.

The catalog plugin name is `beyondwin-skills`. That does not mean a marketplace listing.

## Install paths and hosts

Install, link, and remove steps are in [Installation](installation.md). Verification is in [Verification](verification.md).

Windows-meaningful checks are the Korean-editor offline suite and repository contracts. Do not say `image-workbench` can make or edit images unless that host has its own image tool and you can open the result.

The license is Apache-2.0.

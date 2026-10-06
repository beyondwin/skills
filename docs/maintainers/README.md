# Maintainer docs

This is the guide for people who change this repository. Find your task in the
[Tasks](#tasks) table: it shows what to edit, what to change with it, and how to
check it. For how the tree is split, see [architecture](repository/architecture.md).
Install help for users lives in each product README and in `docs/users/`.

## Tasks

| Task | Edit | Change with it | Check |
| --- | --- | --- | --- |
| Create or improve a skill | Read [skill practices](repository/skill-practices.md) first | Add a rule there only with its evidence | None |
| Change product behavior | `skills/<name>/` | The files-to-change-together list in that product's `contract.md` ([products](products/)), `testing.md`, and the version if needed | `python3 scripts/verify.py --skill <name>` |
| Add host support | That product's `compatibility.md` ([products](products/)) | `products.toml`, public docs, tests | `python3 scripts/verify.py` |
| Register a product | `products.toml` | `skills/<name>/`, `tests/products/<name>/`, `docs/maintainers/products/<name>/`. Steps: [products registry](repository/products-registry.md) | `python3 scripts/verify.py` |
| Bump a version | `skills/<name>/release.toml` | `SKILL.md` `metadata.version`, `CHANGELOG.md`. Rules: [versioning](repository/versioning.md) | `python3 scripts/verify.py --skill <name>` |
| Release a product | Finalize `Unreleased` in `skills/<name>/CHANGELOG.md` | That product's `release.md`. Steps: [release](repository/release.md) | `python3 scripts/release.py check --product <name>` (on a clean tree) |
| Work-in-progress design or plan | `docs/history/` | Delete it when done. See [history](../history/) | None |

Before any merge, run `python3 scripts/verify.py`.

## Writing rules

- Maintainer docs are English only. There is no Korean copy.
- Product `README.md` is English and `README.ko.md` is Korean. User guides live in
  `docs/users/en/` and `docs/users/ko/`.
- `SKILL.md` and runtime `references/` are English because agents run them.
- There are two readers. People who pick and call a skill read the product README.
  People who install, verify, change, or release read `docs/users/` and this
  `docs/maintainers/` index. Put each file in its reader's tree only.
- One doc owns each fact; other pages link to it. `docs/users/` owns public install,
  each `contract.md` and `SKILL.md` own product behavior, and
  `skills/pre-sdd-review/evidence/README.md` owns recorder commands.
- Write short sentences in plain words.
- When you change a current doc, update the test phrase and fact checks in the same
  change. Tests for maintainer and user docs check exact phrases, facts, lists, order,
  and structure (required sections). They never hash a whole doc or section.
- Product behavior changes follow the contract's files-to-change-together list.
- `docs/history/` holds only work-in-progress designs and plans. It does not define
  the current contract.

## Repository docs

| Doc | Covers |
| --- | --- |
| [Architecture](repository/architecture.md) | Payload versus development evidence, check scope |
| [Products registry](repository/products-registry.md) | `products.toml` schema and registration |
| [Versioning](repository/versioning.md) | Product SemVer rules and tags |
| [Release](repository/release.md) | Per-product check, build, and verify-download |
| [Skill practices](repository/skill-practices.md) | Measured rules for writing and changing a skill, and how to measure a change |

## Product docs

Each product has four docs: contract, testing, compatibility, and release. A behavior
change in one product never requires a version bump in another.

| Product | Contract | Testing | Compatibility | Release |
| --- | --- | --- | --- | --- |
| korean-writing-editor | [contract](products/korean-writing-editor/contract.md) | [testing](products/korean-writing-editor/testing.md) | [compatibility](products/korean-writing-editor/compatibility.md) | [release](products/korean-writing-editor/release.md) |
| image-workbench | [contract](products/image-workbench/contract.md) | [testing](products/image-workbench/testing.md) | [compatibility](products/image-workbench/compatibility.md) | [release](products/image-workbench/release.md) |
| how-it-works | [contract](products/how-it-works/contract.md) | [testing](products/how-it-works/testing.md) | [compatibility](products/how-it-works/compatibility.md) | [release](products/how-it-works/release.md) |
| pre-sdd-review | [contract](products/pre-sdd-review/contract.md) | [testing](products/pre-sdd-review/testing.md) | [compatibility](products/pre-sdd-review/compatibility.md) | [release](products/pre-sdd-review/release.md) |
| sddx | [contract](products/sddx/contract.md) | [testing](products/sddx/testing.md) | [compatibility](products/sddx/compatibility.md) | [release](products/sddx/release.md) |
| waygent | [contract](products/waygent/contract.md) | [testing](products/waygent/testing.md) | [compatibility](products/waygent/compatibility.md) | [release](products/waygent/release.md) |

What each doc holds:

- Contract: triggers, defaults, output, safety, files to change together
- Testing: deterministic fixtures, commands, evidence limits
- Compatibility: current hosts, capabilities, evidence bounds, rules for new support
- Release: version source, SemVer examples, check/build/download, failure recovery

Where products differ:

- pre-sdd-review: the contract also covers authority order and verdicts. Testing
  covers provider-free contract fixtures and the evidence limits of the optional live
  run. Compatibility is measured Codex support, with other hosts `not_measured`.
  Release keeps a no-publication boundary.
- sddx: the contract covers the split between host and execution backend, and attempt
  lookup (`status`). Testing uses provider-free identity fixtures. Compatibility
  covers the Claude Code and Codex orchestrators; worker CLIs are not hosts. Release
  keeps a no-publication boundary.
- waygent: the contract lists only the `SKILL.md` promises that tests lock (trailers,
  progress file, review count, branch, same model, line limit). Hosts are Claude Code,
  Codex, and Cursor Agent; measured runs are in the waygent compatibility doc.

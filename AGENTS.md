# Working rules

- Put the user's request and the approved scope first. Make routine choices yourself and finish through implementation and verification. Do not ask again about work that is already approved.
- If a skill's instructions make you stop, name the file, the exact wording, and why it applies. Do not run the procedure of a `SKILL.md` you are editing as if it applied to the current task.
- Check the relevant contracts before you start, and keep any changes already in the working tree.
- Report to the user in Korean, briefly: what changed, what verification actually ran, and what is left.
- Docs are English. Only user-facing READMEs and user guides get a Korean copy (`README.ko.md`, `docs/users/ko/`). Legacy is not supported: delete old paths, names, and shims instead of keeping them working.

## Repository

- How the tree is split: [Architecture](docs/maintainers/repository/architecture.md).
- Products and owned paths: [products.toml](products.toml). Contribution scope: [CONTRIBUTING.md](CONTRIBUTING.md).
- When you edit `skills/<name>/`, check the contracts in `tests/products/<name>/` and `docs/maintainers/products/<name>/`.
- When an installed product file changes, update `skills/<name>/release.toml`, `metadata.version` in `SKILL.md`, and the `Unreleased` section of `CHANGELOG.md` together, per [Versioning](docs/maintainers/repository/versioning.md).
- A supported-host change goes into the product list, the docs, and the tests together.
- A declared set (an enum, a key list, a count, a version literal, a digest) usually lives in several files, and a diff scoped to one file cannot show the others. Before changing one, grep its name across the skill, its maintainer docs and tests, the CHANGELOG, and `scripts/release.py`, and change every copy in the same commit.
- Never commit private source text or images, credentials, provider receipts, or generated media. Run live model calls only within explicitly approved scope.

## Verification

- If you changed only product files, run `python3 scripts/verify.py --skill <name>` first. The required check before merge is `python3 scripts/verify.py`.
- A passing full run on CI Ubuntu is not evidence of macOS support. Run live `--execute` only after that product's runtime or execution contract changed, on macOS, and only when explicitly asked.
- For doc-only changes, check the content, links, and diff. Run the checks that fit the change, and do not repeat a passing check unless something new changed or a concern is still open.
- Default verification runs with no credentials and no provider calls. Do not stretch an offline pass into evidence of real model quality or of runs in other environments.

## Live runs

- Process command lines on this Mac carry other agents' API keys. Do not print `ps aux`, `pgrep -fl`, or `pgrep -a`; `pgrep -f <path>` prints only pids.
- Codex: isolate each run with its own `HOME` and `CODEX_HOME` holding a copy of `auth.json`, and turn memories off so runs share no state. A `$skill` mention also injects the natively installed copy of that skill, so for a pinned copy leave the native one out of the run's home. `codex exec` does not expand `$skill` for an explicit-only skill.
- The model and effort in `~/.codex/config.toml` are not always what runs (on 2026-10-02 it named `gpt-6.1-sol`/low, which a ChatGPT account rejects, while 12 of the last 15 sessions ran `gpt-6-astra`/high). Read what ran from the rollout's `turn_context` (`skills/sddx/scripts/observed_model.py`).
- `/usr/bin/python3` on stock macOS is 3.9, and product scripts have broken on it (`910bd21`). Keep product scripts free of newer syntax.

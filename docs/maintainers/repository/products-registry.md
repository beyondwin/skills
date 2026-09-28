# Products registry

`products.toml` is the single ordered index of current standalone products. Edit it
when you add a product or change its folders or supported hosts. It is the source for
names, folders, and hosts. It does not own versions, tags, or shell commands; each
product's version source is `skills/<name>/release.toml`.

## Schema

Only the fields below are allowed. Extra keys, missing keys, or wrong types make the
load fail. No field is optional.

The only allowed top-level keys are `schema_version` and `products`.
`schema_version` must be the exact integer `1`, not a bool. `supported_hosts`,
`owned_paths`, and `verify_stages` are required non-empty lists. Duplicates within a
list, and duplicate names or paths across products, are rejected. An empty stage
selection also fails closed.

| Field | Level | Meaning |
| --- | --- | --- |
| `schema_version` | top | Must be `1` |
| `name` | product | Product ID; matches the folder, `SKILL.md` `name`, and `release.toml` name. `^[a-z0-9]+(?:-[a-z0-9]+)*$` |
| `display_name` | product | Human-readable name |
| `skill_path` | product | Payload folder. Repository-relative; no `..` or absolute paths |
| `test_path` | product | Product test folder |
| `maintainer_docs` | product | Product maintainer docs folder |
| `supported_hosts` | product | Allowed values: `codex`, `claude-code`, `cursor`, `grok` |
| `owned_paths` | product | Change-routing prefixes. Folder entries end with `/` |
| `verify_stages` | product | Stage IDs registered in code. Not shell commands |

There are no `version`, `tag_prefix`, or `command` fields. The parser
(`scripts/lib/product_registry.py`) enforces product order and rejects duplicate names
and paths.

When you change supported hosts, update that product's `compatibility.md`, product
README, public guides, and tests in the same change.

## Doc languages

Every product follows the same rule. `skills/<name>/README.md` is English,
`skills/<name>/README.ko.md` is Korean, and `docs/maintainers/products/<name>/` is
English. The file names live in one place, `PRODUCT_README_NAMES` in
`scripts/lib/product_registry.py`; verification, link checks, and repository tests use
it.

Both READMEs ship in the payload. Any other README file fails as an unexpected top-level file. Public guides link `README.ko.md` for Korean
and `README.md` for English.

## Registering a product

To add a standalone product, do all of this in one change:

1. Add the product entry to `products.toml`.
2. Create `skills/<name>/`, `tests/products/<name>/`, and
   `docs/maintainers/products/<name>/`.
3. Add the four maintainer docs: `contract.md`, `testing.md`, `compatibility.md`,
   `release.md`.
4. List registered stage IDs in `verify_stages`.
5. Make registry validation pass.

These all fail verification: an unregistered folder under `skills/`,
`tests/products/`, or `docs/maintainers/products/`; an unknown host or stage; a name
mismatch.

## Verification commands

Every verification command first reads `products.toml` and checks it with
`validate_registry`.

```bash
python3 scripts/verify.py
python3 scripts/verify.py --skill <name>
```

With any selector, `products.toml` is checked against the stage names registered in
code. On an error it exits with code 1 before running any stage.

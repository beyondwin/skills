# Independent Skill Product Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the repository into a monorepo of independently versioned, documented, verified, and packaged skill products with a separately versioned catalog bundle.

**Architecture:** Each `skills/<name>/` directory owns its release manifest, product documentation, changelog, and runtime payload. Production Python modules validate product and catalog contracts; release code packages one product at a time or assembles a catalog only from locked standalone release inputs. The repository root remains the source for individual GitHub-path installs, while plugin metadata moves under `catalog/plugin/` so current skill development cannot silently change an older catalog release.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `tomllib`, `unittest`, `zipfile`), Markdown, TOML, JSON, Git, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-27-independent-skill-product-architecture-design.md`

## Global Constraints

- Preserve the existing individual install URLs under `skills/korean-writing-editor`, `skills/image-workbench`, and `skills/graspic`.
- Preserve `python3 scripts/verify.py` and `python3 scripts/verify.py --profile windows-portable` as full-repository commands.
- Keep required CI provider-free, credential-free, telemetry-free, and free of model or remote image calls.
- Do not change the runtime behavior of any skill as part of this migration; preserve commit `4be206f` and the approved `graspic` target version `3.0.0`.
- Set the next standalone targets to `korean-writing-editor 2.0.1`, `image-workbench 2.0.1`, and `graspic 3.0.0`.
- Keep the local catalog pinned to the published legacy `v2.0.0` until independent standalone releases exist; `beyondwin-skills 2.1.0` adoption is a later explicitly authorized release operation.
- Preserve public tag `v2.0.0` at commit `78a8b1bf37d1b943f4b8337121b556eeaea926ae` and never move or recreate it.
- Use only the Python standard library; do not add PyPI, Node, provider, or GitHub Action dependencies.
- Build from tracked regular files only. Reject symlinks, special files, unsafe paths, duplicate names, case-fold collisions, and nonempty output directories.
- Keep live Korean and image evaluations opt-in and outside required CI.
- Do not push, create tags, publish GitHub Releases, mutate Archive, or perform any other external write while executing this plan.
- Preserve unrelated work. If an in-scope routine defect or test failure appears, diagnose it, add a regression test, and fix it without asking the user; stop only for missing authority, credentials, or an irreversible external operation.

---

## Target File Map

### Production contracts and release code

- `scripts/release_contract.py` — product manifest parsing, payload validation, normalized payload hashing, and staging.
- `scripts/catalog_contract.py` — catalog release and lock parsing, schema validation, and locked-input validation.
- `scripts/catalog_lock.py` — one-time import of the published legacy standalone assets into `catalog/catalog.lock.json`.
- `scripts/release_archive.py` — deterministic ZIP, checksum, extraction, and archive-safety primitives.
- `scripts/release.py` — public `check`, `build`, and `verify-download` CLI for a product or catalog.
- `scripts/build_release.py` — one-minor compatibility wrapper that fails closed and points to `scripts/release.py`.
- `scripts/changed_targets.py` — fail-closed changed-path to CI-target mapping.
- `scripts/verify.py` — full, product-specific, and catalog-specific provider-free orchestration.

### Product-owned files

- `skills/<name>/release.toml` — authoritative current target version and tag prefix.
- `skills/<name>/README.md` — Korean user source document.
- `skills/<name>/README.en.md` — English public-core document.
- `skills/<name>/CHANGELOG.md` — product-only release history and Unreleased changes.
- `skills/<name>/SKILL.md` — runtime contract whose `metadata.version` mirrors `release.toml`.

### Catalog-owned files

- `catalog/release.toml` — catalog release identity.
- `catalog/catalog.lock.json` — last published catalog's immutable skill inputs.
- `catalog/plugin/.codex-plugin/plugin.json` — plugin manifest source copied to ZIP root at build time.
- `catalog/README.md` and `catalog/CHANGELOG.md` — catalog purpose and history.

### Documentation

- `docs/users/{ko,en}/` — paired shared installation, compatibility, safety/privacy, and verification guides.
- `docs/maintainers/repository/` — repository architecture, versioning, catalog release, and Archive provenance.
- `docs/maintainers/<name>/` — product contract, testing, and release protocols.
- Existing `docs/{ko,en}/` paths — one-minor redirect stubs only.

---

### Task 1: Make Archive provenance immune to Git URL rewrites

**Files:**
- Modify: `scripts/capture_archive_manifest.py:58-59`
- Modify: `tests/contract/test_archive_manifest.py:52-86`

**Interfaces:**
- Consumes: Git's literal `remote.origin.url` configuration.
- Produces: `remote_url(repository: Path) -> str`, returning the configured canonical URL without applying `url.*.insteadOf` rewrites.

- [ ] **Step 1: Add a failing regression test for the observed rewrite**

Add this test to `ArchiveManifestTests`:

```python
def test_build_manifest_uses_literal_remote_when_instead_of_rewrites_get_url(self) -> None:
    run_git(
        self.repository,
        "config",
        "url.git@github-beyondwin:.insteadOf",
        "https://github.com/",
    )
    self.assertEqual(
        run_git(self.repository, "remote", "get-url", "origin"),
        "git@github-beyondwin:beyondwin/Archive.git",
    )
    manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
    self.assertEqual(
        manifest["source_repository"],
        "https://github.com/beyondwin/Archive.git",
    )
```

- [ ] **Step 2: Run the regression test and confirm RED**

Run:

```bash
python3 -m unittest tests.contract.test_archive_manifest.ArchiveManifestTests.test_build_manifest_uses_literal_remote_when_instead_of_rewrites_get_url
```

Expected: FAIL because `git remote get-url origin` applies the rewrite.

- [ ] **Step 3: Read the literal remote config instead of the rewritten URL**

Replace `remote_url` with:

```python
def remote_url(repository: Path) -> str:
    value = git(repository, "config", "--get", "remote.origin.url")
    if not value:
        raise CaptureError("missing remote.origin.url")
    return value
```

- [ ] **Step 4: Run the focused and full Archive tests**

Run:

```bash
python3 -m unittest tests.contract.test_archive_manifest.ArchiveManifestTests.test_build_manifest_uses_literal_remote_when_instead_of_rewrites_get_url
python3 -m unittest tests.contract.test_archive_manifest
```

Expected: both PASS.

- [ ] **Step 5: Commit the provenance fix**

```bash
git add scripts/capture_archive_manifest.py tests/contract/test_archive_manifest.py
git commit -m "fix: preserve canonical archive remote identity"
```

---

### Task 2: Establish independent product release contracts

**Files:**
- Create: `scripts/release_contract.py`
- Create: `tests/contract/test_release_contract.py`
- Create: `skills/korean-writing-editor/release.toml`
- Create: `skills/korean-writing-editor/CHANGELOG.md`
- Create: `skills/image-workbench/release.toml`
- Create: `skills/image-workbench/CHANGELOG.md`
- Create: `skills/graspic/release.toml`
- Create: `skills/graspic/CHANGELOG.md`
- Replace: `scripts/build_release.py` with a fail-closed migration wrapper
- Modify: `skills/korean-writing-editor/SKILL.md:6-8`
- Modify: `skills/image-workbench/SKILL.md:6-8`
- Modify: `tests/contract/test_korean_package.py:56-66`
- Modify: `tests/image-workbench/run.py:38-52`
- Modify: `tests/contract/test_release.py`
- Modify: `tests/contract/test_repository.py:13-115,306-371`

**Interfaces:**
- Consumes: a `skills/<name>/` directory containing tracked product files.
- Produces: `ProductRelease`, `load_product_release`, `validate_product`, `payload_entries`, `payload_sha256`, and `stage_product`.

- [ ] **Step 1: Write failing product-contract tests**

Create `tests/contract/test_release_contract.py` with these core cases:

```python
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.release_contract import (
    PRODUCT_NAMES,
    ProductRelease,
    load_product_release,
    payload_sha256,
    validate_product,
)

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "korean-writing-editor": "2.0.1",
    "image-workbench": "2.0.1",
    "graspic": "3.0.0",
}


class ProductReleaseTests(unittest.TestCase):
    def test_each_product_owns_an_independent_release_manifest(self) -> None:
        self.assertEqual(set(PRODUCT_NAMES), set(EXPECTED))
        for name, version in EXPECTED.items():
            release = load_product_release(ROOT / "skills" / name)
            self.assertIsInstance(release, ProductRelease)
            self.assertEqual(release.name, name)
            self.assertEqual(release.version, version)
            self.assertEqual(release.tag, f"{name}-v{version}")
            self.assertEqual(validate_product(release.root), [])

    def test_one_product_version_can_change_without_changing_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "graspic"
            shutil.copytree(ROOT / "skills" / "graspic", root)
            manifest = root / "release.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace('version = "3.0.0"', 'version = "3.0.1"'),
                encoding="utf-8",
            )
            errors = validate_product(root)
            self.assertIn("release.toml version 3.0.1 != SKILL.md version 3.0.0", errors)

    def test_payload_hash_changes_with_bytes_but_is_stable_across_copies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = ROOT / "skills" / "image-workbench"
            copy = Path(directory) / "image-workbench"
            shutil.copytree(original, copy)
            self.assertEqual(payload_sha256(original), payload_sha256(copy))
            before = payload_sha256(copy)
            skill_md = copy / "SKILL.md"
            skill_md.write_text(skill_md.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertNotEqual(before, payload_sha256(copy))
```

Also add rejection cases for invalid SemVer, mismatched directory/name, missing CHANGELOG, missing license, symlink, special file, unsafe relative link, unexpected top-level file, and dated-release validation.

- [ ] **Step 2: Run the new module and confirm RED**

Run:

```bash
python3 -m unittest tests.contract.test_release_contract
```

Expected: ERROR because `scripts.release_contract` and product manifests do not exist.

- [ ] **Step 3: Implement the product release model and payload validator**

Create `scripts/release_contract.py` with these public signatures:

```python
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
import shutil
import stat
import tomllib
from pathlib import Path

PRODUCT_NAMES = (
    "korean-writing-editor",
    "image-workbench",
    "graspic",
)
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
ALLOWED_TOP_LEVEL = frozenset({
    "SKILL.md",
    "README.md",
    "README.en.md",
    "CHANGELOG.md",
    "release.toml",
    "LICENSE.txt",
    "agents",
    "references",
    "scripts",
})


@dataclasses.dataclass(frozen=True)
class ProductRelease:
    root: Path
    name: str
    version: str
    tag_prefix: str
    license: str

    @property
    def tag(self) -> str:
        return f"{self.tag_prefix}{self.version}"

    @property
    def artifact_name(self) -> str:
        return f"{self.name}-v{self.version}.zip"


def load_product_release(skill_root: Path) -> ProductRelease:
    skill_root = Path(skill_root)
    data = tomllib.loads((skill_root / "release.toml").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("release.toml schema_version must be 1")
    return ProductRelease(
        root=skill_root,
        name=str(data["name"]),
        version=str(data["version"]),
        tag_prefix=str(data["tag_prefix"]),
        license=str(data["license"]),
    )


def payload_sha256(skill_root: Path) -> str:
    encoded = (
        json.dumps(
            payload_entries(skill_root),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
```

Move `_parse_frontmatter`, `_validate_openai_yaml`, `_check_relative_links`, `_iter_payload_paths`, `validate_skill`, and `stage_skill` from `tests/contract/test_repository.py` into this production module. Rename the public functions to `parse_skill_frontmatter`, `validate_product`, and `stage_product`, then replace the shared `EXPECTED_VERSION` comparison with `release.toml` versus `SKILL.md metadata.version`. `payload_entries` must sort POSIX relative paths and record `path`, normalized `mode` (`0644` or `0755`), `size`, and file SHA-256. Ignore only validated `__pycache__`, `.pyc`, and `.pyo` residue; reject every other unexpected entry. Permit product README files in the allowlist but do not require them until Task 8 migrates public documentation.

- [ ] **Step 4: Add authoritative manifests and independent changelogs**

Use these exact manifests:

```toml
# skills/korean-writing-editor/release.toml
schema_version = 1
name = "korean-writing-editor"
version = "2.0.1"
tag_prefix = "korean-writing-editor-v"
license = "Apache-2.0"
```

```toml
# skills/image-workbench/release.toml
schema_version = 1
name = "image-workbench"
version = "2.0.1"
tag_prefix = "image-workbench-v"
license = "Apache-2.0"
```

```toml
# skills/graspic/release.toml
schema_version = 1
name = "graspic"
version = "3.0.0"
tag_prefix = "graspic-v"
license = "Apache-2.0"
```

Each CHANGELOG must start with `# Changelog` and `## Unreleased`. The Korean and image changelogs must record their public legacy `2.0.0` standalone asset under tag `v2.0.0` without inventing an individual tag. The graspic changelog must record the artifact-page contract as an unreleased breaking change and state that no public graspic release exists yet.

- [ ] **Step 5: Retire the unsafe shared-version builder immediately**

Replace `scripts/build_release.py` with a compatibility wrapper that prints this exact message to stderr and exits `2` without creating output:

```text
scripts/build_release.py no longer builds a shared-version bundle. Use scripts/release.py after the independent release pipeline lands.
```

Replace bundle-generation assertions in `tests/contract/test_release.py` with assertions for the exact message, exit code `2`, and zero created files. Task 5 will add the independent builder tests.

- [ ] **Step 6: Update mirrored SKILL versions and productionize repository validation**

Change Korean and image `metadata.version` to `2.0.1` and `updated_at` to `2026-08-27`. Keep graspic at `3.0.0`. Update the Korean package assertion and image evaluator's synthetic valid frontmatter to their product's `2.0.1`. Replace the local validator implementation in `tests/contract/test_repository.py` with imports from `scripts.release_contract`; remove `EXPECTED_VERSION`, the test-only frontmatter parser, and the rule that all products share one version. Update stage tests so CHANGELOG and release.toml are required and README names are permitted. Task 8 will make the README pair mandatory after creating it.

- [ ] **Step 7: Run RED-to-GREEN product contract verification**

Run:

```bash
python3 -m unittest tests.contract.test_release_contract
python3 -m unittest tests.contract.test_repository
python3 scripts/verify.py
```

Expected: all PASS. If the full verifier exposes another in-scope contract drift, add a focused failing test before fixing it.

- [ ] **Step 8: Commit independent product roots**

```bash
git add scripts/release_contract.py scripts/build_release.py tests/contract/test_release_contract.py tests/contract/test_release.py tests/contract/test_repository.py tests/contract/test_korean_package.py tests/image-workbench/run.py skills/korean-writing-editor skills/image-workbench skills/graspic
git commit -m "feat: establish independent skill release contracts"
```

---

### Task 3: Separate catalog source from current skill development

**Files:**
- Create: `scripts/catalog_contract.py`
- Create: `scripts/catalog_lock.py`
- Create: `tests/contract/test_catalog_contract.py`
- Create: `catalog/release.toml`
- Create: `catalog/README.md`
- Move and rewrite: `CHANGELOG.md` to `catalog/CHANGELOG.md`
- Create: `catalog/catalog.lock.json` through the migration command
- Create: `catalog/plugin/.codex-plugin/plugin.json`
- Delete: `.codex-plugin/plugin.json`
- Modify: `docs/maintainers/architecture.md`
- Modify: `docs/maintainers/release-process.md`
- Modify: `tests/contract/test_public_docs.py`
- Modify: `tests/contract/test_repository.py`

**Interfaces:**
- Consumes: published standalone ZIPs plus `SHA256SUMS` and the pinned source commit.
- Produces: `CatalogRelease`, `LockedSkill`, `CatalogLock`, `load_catalog_release`, `load_catalog_lock`, and `validate_catalog`.

- [ ] **Step 1: Add failing catalog schema and ownership tests**

Create tests that assert:

```python
class CatalogContractTests(unittest.TestCase):
    def test_plugin_manifest_is_owned_below_catalog(self) -> None:
        self.assertFalse((ROOT / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue(
            (ROOT / "catalog" / "plugin" / ".codex-plugin" / "plugin.json").is_file()
        )

    def test_legacy_lock_pins_exactly_the_two_v2_products(self) -> None:
        lock = load_catalog_lock(ROOT / "catalog" / "catalog.lock.json")
        self.assertEqual([item.name for item in lock.skills], [
            "image-workbench",
            "korean-writing-editor",
        ])
        self.assertTrue(all(item.release_kind == "legacy-bundle" for item in lock.skills))
        self.assertTrue(all(item.tag == "v2.0.0" for item in lock.skills))
        self.assertTrue(all(item.source_commit == "78a8b1bf37d1b943f4b8337121b556eeaea926ae" for item in lock.skills))
```

Add rejection tests for unsorted names, duplicate products, invalid release kind, malformed commit/hash, a legacy entry for graspic, and an independent entry whose tag is not `<name>-v<version>`.

- [ ] **Step 2: Run the catalog tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_catalog_contract
```

Expected: ERROR because catalog modules and files do not exist.

- [ ] **Step 3: Implement catalog dataclasses and fail-closed schema validation**

Use these public types:

```python
@dataclasses.dataclass(frozen=True)
class CatalogRelease:
    root: Path
    name: str
    version: str
    tag_prefix: str


@dataclasses.dataclass(frozen=True)
class LockedSkill:
    name: str
    version: str
    tag: str
    release_kind: str
    source_commit: str
    payload_sha256: str


@dataclasses.dataclass(frozen=True)
class CatalogLock:
    schema_version: int
    skills: Sequence[LockedSkill]


def load_catalog_release(path: Path) -> CatalogRelease:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return CatalogRelease(
        root=Path(path).parent,
        name=str(data["name"]),
        version=str(data["version"]),
        tag_prefix=str(data["tag_prefix"]),
    )


def load_catalog_lock(path: Path) -> CatalogLock:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    skills = tuple(LockedSkill(**item) for item in data["skills"])
    return CatalogLock(schema_version=int(data["schema_version"]), skills=skills)
```

Import `Sequence` from `collections.abc`. Implement `validate_catalog(root: Path) -> list[str]` to reject unknown keys before constructing dataclasses, then enforce sorted unique product names, schema `1`, valid SemVer, lowercase 40-character commit IDs, lowercase 64-character payload hashes, and catalog/plugin version equality. Permit `legacy-bundle` only for Korean and image at version `2.0.0`, tag `v2.0.0`, and pinned commit `78a8b1bf37d1b943f4b8337121b556eeaea926ae`. Permit `independent` only with a product-qualified tag.

- [ ] **Step 4: Move the exact legacy plugin manifest under catalog ownership**

Create `catalog/plugin/.codex-plugin/plugin.json` with the exact bytes from `git show v2.0.0:.codex-plugin/plugin.json`, then delete the root manifest with `apply_patch`. Create `catalog/release.toml` with version `2.0.0` and tag prefix `beyondwin-skills-v`. Move the public `2.0.0` history from root `CHANGELOG.md` to `catalog/CHANGELOG.md`, replace the stale graspic `2.0.0` Unreleased entry with an empty catalog Unreleased section, and remove the root changelog. The catalog README must state that only released plugin ZIPs are supported catalog artifacts; the repository root is for individual skill installs. Update the current flat architecture and release-process documents plus their tests immediately so no active document claims the root still owns plugin metadata; Task 9 will relocate and expand those documents.

- [ ] **Step 5: Implement and test the one-time legacy lock importer**

`scripts/catalog_lock.py` must expose `import_legacy_release(release_dir: Path, source_commit: str, output: Path) -> Path`. It must verify the downloaded `SHA256SUMS`, accept exactly the Korean and image standalone ZIPs from `v2.0.0`, reject absolute paths, backslashes, empty segments, dot segments, parent segments, duplicates, case-fold collisions, symlinks, and special files before extraction, compute normalized product payload hashes, sort entries by name, and write canonical JSON through a same-directory temporary file followed by `Path.replace`. It must not contact the network itself. Task 5 moves these archive-safety primitives into the shared production module and changes this importer to reuse them.

The importer must require and verify the checksum rows for those two standalone ZIPs while tolerating unrelated rows in the published `SHA256SUMS`; unrelated assets need not be present in the import directory. Any third local ZIP or any unexpected local file still fails closed.

- [ ] **Step 6: Generate the real legacy lock from fresh public bytes**

Run:

```bash
legacy_release_dir=$(mktemp -d)
gh release download v2.0.0 --repo beyondwin/skills --pattern 'korean-writing-editor-v2.0.0.zip' --pattern 'image-workbench-v2.0.0.zip' --pattern 'SHA256SUMS' --dir "$legacy_release_dir"
python3 scripts/catalog_lock.py import-legacy --release-dir "$legacy_release_dir" --source-commit 78a8b1bf37d1b943f4b8337121b556eeaea926ae --output catalog/catalog.lock.json
```

Expected: the command verifies public checksums and writes two sorted `legacy-bundle` entries. Do not commit downloaded ZIPs or temporary evidence.

- [ ] **Step 7: Run catalog and repository tests**

```bash
python3 -m unittest tests.contract.test_catalog_contract
python3 -m unittest tests.contract.test_repository tests.contract.test_public_docs
git diff --check
```

Expected: PASS and no root plugin manifest.

- [ ] **Step 8: Commit catalog ownership and legacy provenance**

```bash
git add -A -- catalog CHANGELOG.md scripts/catalog_contract.py scripts/catalog_lock.py docs/maintainers/architecture.md docs/maintainers/release-process.md tests/contract/test_catalog_contract.py tests/contract/test_public_docs.py tests/contract/test_repository.py .codex-plugin
git commit -m "feat: separate catalog release ownership"
```

---

### Task 4: Add product-specific and catalog-specific verification

**Files:**
- Modify: `scripts/verify.py:14-147`
- Modify: `tests/contract/test_verify.py:15-281`

**Interfaces:**
- Consumes: `--profile`, optional `--skill`, and optional `--catalog`.
- Produces: `stages(profile: str, *, skill: str | None = None, catalog: bool = False) -> Sequence[Stage]`.

- [ ] **Step 1: Add failing CLI selection tests**

Add tests for all products and mutual exclusion:

```python
def test_graspic_selection_runs_only_shared_and_graspic_gates(self) -> None:
    verify = self._load()
    names = [stage.name for stage in verify.stages("full", skill="graspic")]
    self.assertEqual(names, ["product-contract", "graspic-contract", "python-compile"])

def test_catalog_selection_runs_catalog_gates_only(self) -> None:
    verify = self._load()
    names = [stage.name for stage in verify.stages("full", catalog=True)]
    self.assertEqual(names, ["catalog-contract", "python-compile"])

def test_skill_and_catalog_are_mutually_exclusive(self) -> None:
    verify = self._load()
    with self.assertRaises(ValueError):
        verify.stages("full", skill="graspic", catalog=True)
```

Add exact stage-order assertions for Korean and image, plus CLI exit tests for an unknown skill and conflicting selectors.

- [ ] **Step 2: Run verification module tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_verify
```

Expected: FAIL because `stages` does not accept selectors.

- [ ] **Step 3: Implement target-specific stage catalogs**

Keep `stages("full")` and `stages("windows-portable")` byte-for-byte compatible in stage order. Add:

```python
PRODUCT_STAGE_NAMES = {
    "korean-writing-editor": (
        "product-contract",
        "korean-package",
        "korean-offline",
        "korean-live-unit",
        "korean-live-dry-run",
        "python-compile",
    ),
    "image-workbench": (
        "product-contract",
        "image-contract",
        "image-inspector",
        "python-compile",
    ),
    "graspic": (
        "product-contract",
        "graspic-contract",
        "python-compile",
    ),
}
CATALOG_STAGE_NAMES = ("catalog-contract", "python-compile")
```

`product-contract` must call `python -m unittest tests.contract.test_release_contract`; product-specific stages must invoke existing product suites. Apply the Windows exclusions after selecting names.

- [ ] **Step 4: Add mutually exclusive CLI flags**

Use one argparse mutually exclusive group:

```python
target = parser.add_mutually_exclusive_group()
target.add_argument("--skill", choices=PRODUCT_NAMES)
target.add_argument("--catalog", action="store_true")
```

Do not shell-compose commands. Every stage must continue to use `sys.executable` and tuple argv.

- [ ] **Step 5: Run all verification-selection tests and target smokes**

```bash
python3 -m unittest tests.contract.test_verify
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py --skill image-workbench
python3 scripts/verify.py --skill graspic
python3 scripts/verify.py --catalog
python3 scripts/verify.py
```

Expected: all PASS.

- [ ] **Step 6: Commit verification targeting**

```bash
git add scripts/verify.py tests/contract/test_verify.py
git commit -m "feat: verify skills independently"
```

---

### Task 5: Build one deterministic product release at a time

**Files:**
- Create: `scripts/release_archive.py`
- Create: `scripts/release.py`
- Modify: `scripts/catalog_lock.py`
- Rewrite: `tests/contract/test_release.py`
- Modify: `tests/contract/test_catalog_contract.py`

**Interfaces:**
- Consumes: one validated product root and a new empty output directory.
- Produces: `build_product`, `verify_product_archive`, `extract_archive`, `write_checksums`, and the `release.py check|build` CLI.

- [ ] **Step 1: Replace bundle-coupled tests with failing product build tests**

The new test module must include:

```python
def test_build_product_emits_only_requested_product_and_checksums(self) -> None:
    artifacts = release.build_product(ROOT, "graspic", self.output, require_release_entry=False)
    self.assertEqual(
        {path.name for path in artifacts},
        {"graspic-v3.0.0.zip", "SHA256SUMS"},
    )
    names = release_archive.zip_names(self.output / "graspic-v3.0.0.zip")
    self.assertTrue(all(name.startswith("graspic/") for name in names))
    self.assertIn("graspic/release.toml", names)
    self.assertNotIn("korean-writing-editor/SKILL.md", names)

def test_build_rejects_nonempty_output(self) -> None:
    (self.output / "keep.txt").write_text("keep\n", encoding="utf-8")
    with self.assertRaises(release_archive.ReleaseError):
        release.build_product(ROOT, "image-workbench", self.output, require_release_entry=False)
```

Retain safety tests for absolute paths, `..`, duplicates, case-fold collisions, special files, normalized modes, sorted members, fixed epoch, and byte-identical repeated builds.

- [ ] **Step 2: Run release tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_release
```

Expected: ERROR because the new modules do not exist.

- [ ] **Step 3: Extract deterministic archive primitives from the legacy builder**

Move and tighten the pure ZIP/checksum/extraction behavior into `scripts/release_archive.py`. Define the shared member type exactly as:

```python
@dataclasses.dataclass(frozen=True)
class ArchiveMember:
    name: str
    data: bytes
    executable: bool
```

Recover `ReleaseError`, `zip_info`, `zip_names`, `hashes`, `write_checksums`, `_write_zip`, `_member_safety_errors`, `_member_mode_errors`, `_is_absolute_member`, `_parse_checksums`, and `extract_archive` from parent commit `8ee8c01:scripts/build_release.py`. Rename `_write_zip` to `write_zip`, add `sha256_file`, `verify_product_archive`, and `ensure_new_empty_directory`, and keep all current safety checks. Replace the temporary archive-safety code in `scripts/catalog_lock.py` with imports from `release_archive`; retain catalog tests proving the same rejection behavior. Do not import a test module from production code.

- [ ] **Step 4: Implement product check and build operations**

`scripts/release.py` must expose `check_product(root: Path, name: str, require_dated_changelog: bool) -> list[str]` and `build_product(root: Path, name: str, output: Path, require_release_entry: bool = True) -> tuple[Path, Path]`. `check_product` validates the product, verifies the working tree is clean for that product and shared release code, rejects an existing product-qualified tag, and confirms the target version is greater than its latest independent or legacy baseline. It must compare the current normalized payload with the latest local baseline tag and fail when bytes changed but the version did not advance. `build_product` reads tracked blobs through `git ls-files -s` and `git cat-file blob`, stages exactly one top-level product directory, runs extracted product validation, and writes one ZIP plus `SHA256SUMS`.

- [ ] **Step 5: Add the public CLI without external side effects**

Support these exact forms:

```bash
python3 scripts/release.py check --product graspic
graspic_output_dir=$(mktemp -d)
python3 scripts/release.py build --product graspic --output "$graspic_output_dir"
```

`build` requires a dated current-version CHANGELOG entry. Tests may call `build_product(ROOT, "graspic", output, require_release_entry=False)` only to prove packaging before release preparation. Neither command creates tags, calls GitHub, pushes, or edits source files.

- [ ] **Step 6: Run release safety and reproducibility tests before committing**

```bash
python3 -m unittest tests.contract.test_release
```

Expected: PASS. The real `build` command remains correctly blocked until a dated release entry is prepared.

- [ ] **Step 7: Commit independent product packaging**

```bash
git add scripts/release_archive.py scripts/release.py scripts/catalog_lock.py tests/contract/test_release.py tests/contract/test_catalog_contract.py
git commit -m "feat: build standalone skill releases independently"
```

- [ ] **Step 8: Run clean-tree product readiness checks**

```bash
python3 scripts/release.py check --product korean-writing-editor
python3 scripts/release.py check --product image-workbench
python3 scripts/release.py check --product graspic
```

Expected: all PASS now that product and shared release files are committed and clean. If a check exposes an in-scope defect, add a focused regression test, fix it, rerun the three commands, and create a follow-up fix commit before review.

---

### Task 6: Verify downloaded product bytes

**Files:**
- Modify: `scripts/release.py`
- Modify: `tests/contract/test_release.py`

**Interfaces:**
- Consumes: one fresh directory containing exactly one product ZIP and `SHA256SUMS`.
- Produces: `verify_product_download(root, name, directory) -> list[str]`.

- [ ] **Step 1: Add failing download-integrity tests**

Add tests that accept a valid two-file download directory and reject a missing checksum, malformed digest, extra ZIP, renamed ZIP, checksum mismatch, unsafe member, metadata version mismatch, and extracted validation failure.

```python
def test_verify_product_download_rejects_another_products_zip(self) -> None:
    release.build_product(ROOT, "graspic", self.output, require_release_entry=False)
    (self.output / "image-workbench-v2.0.1.zip").write_bytes(b"not a zip")
    errors = release.verify_product_download(ROOT, "graspic", self.output)
    self.assertIn("unexpected zip in download directory: image-workbench-v2.0.1.zip", errors)
```

- [ ] **Step 2: Run the focused tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_release.ProductDownloadTests
```

Expected: ERROR because `verify_product_download` is absent.

- [ ] **Step 3: Implement fresh-download verification**

Add:

```python
def verify_product_download(root: Path, name: str, directory: Path) -> list[str]:
    release = load_product_release(root / "skills" / name)
    # Parse exactly one expected checksum entry, verify bytes, verify archive,
    # extract into TemporaryDirectory, validate the product, then run its smoke.
```

Implement the body fully. Korean must run its offline evaluator, image must run its evaluator and inspector tests with `IMAGE_WORKBENCH_INSPECTOR` bound to the extracted script, and graspic must run extracted contract validation. No provider call is allowed.

- [ ] **Step 4: Add the verify-download CLI form**

The parser form is `verify-download --product graspic --input PATH`, where `PATH` must be a fresh directory containing only `graspic-v3.0.0.zip` and `SHA256SUMS`. Make `--output` and `--input` subcommand-specific. Reject unexpected files instead of ignoring them.

- [ ] **Step 5: Run product download and legacy-wrapper tests**

```bash
python3 -m unittest tests.contract.test_release
obsolete_output_dir=$(mktemp -d)
python3 scripts/build_release.py --version 2.0.0 --output "$obsolete_output_dir"
```

Expected: unittest PASS; the Task 2 wrapper still exits `2` and creates no output.

- [ ] **Step 6: Commit remote-byte verification**

```bash
git add scripts/release.py tests/contract/test_release.py
git commit -m "feat: verify standalone release downloads"
```

---

### Task 7: Assemble catalog bundles only from locked standalone inputs

**Files:**
- Modify: `scripts/catalog_contract.py`
- Modify: `scripts/release.py`
- Create: `tests/contract/test_catalog_release.py`
- Modify: `scripts/verify.py`
- Modify: `tests/contract/test_verify.py`

**Interfaces:**
- Consumes: `catalog/catalog.lock.json`, catalog plugin metadata, root LICENSE/NOTICE, and a fresh directory of locked standalone ZIPs plus checksums.
- Produces: `validate_catalog_inputs`, `build_catalog`, `verify_catalog_download`, and catalog CLI forms.

- [ ] **Step 1: Write failing catalog-input and bundle tests**

Cover both legacy and independent fixtures. The decisive isolation test is:

```python
def test_catalog_build_uses_locked_archives_not_current_skill_source(self) -> None:
    before = build_catalog(ROOT, self.legacy_inputs, self.output_one)
    with mock.patch.object(Path, "read_bytes", autospec=True, wraps=Path.read_bytes) as read_bytes:
        after = build_catalog(ROOT, self.legacy_inputs, self.output_two)
    self.assertEqual(sha256_file(before[0]), sha256_file(after[0]))
    current_skill_paths = [
        str(call.args[0])
        for call in read_bytes.call_args_list
        if call.args and "/skills/" in str(call.args[0])
    ]
    self.assertEqual(current_skill_paths, [])
```

Also reject a missing locked ZIP, extra product, wrong source version, wrong payload hash, `legacy-bundle` graspic, current-source fallback, plugin members not equal to lock, and non-byte-equivalent standalone payload.

- [ ] **Step 2: Run catalog release tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_catalog_release
```

Expected: ERROR because catalog build functions are absent.

- [ ] **Step 3: Validate locked release inputs**

Implement `validate_catalog_inputs(root: Path, input_dir: Path) -> list[str]`, `build_catalog(root: Path, input_dir: Path, output: Path) -> tuple[Path, Path]`, and `verify_catalog_download(root: Path, directory: Path) -> list[str]`. For `independent`, require embedded `release.toml`, product-qualified tag semantics, checksum, normalized payload hash, and product smoke. For `legacy-bundle`, accept only the pinned `v2.0.0` Korean and image archives, validate embedded SKILL versions, and compare normalized hashes. Prefix extracted standalone members with `skills/` in the plugin ZIP; copy the nested catalog manifest to ZIP-root `.codex-plugin/plugin.json`.

- [ ] **Step 4: Add catalog CLI forms**

Support `check --catalog --input PATH`, `build --catalog --input PATH --output PATH`, and `verify-download --catalog --input PATH`. Product and catalog selectors must be mutually exclusive. Catalog build emits only `beyondwin-skills-v2.0.0.zip` and `SHA256SUMS` for the pinned legacy lock.

- [ ] **Step 5: Add catalog release verification to `verify.py --catalog`**

Append `catalog-release-contract` after `catalog-contract` and before `python-compile`. The stage runs `python -m unittest tests.contract.test_catalog_release` and performs no network access.

- [ ] **Step 6: Exercise the builder with fresh public legacy inputs**

```bash
catalog_public_dir=$(mktemp -d)
catalog_input_dir=$(mktemp -d)
catalog_output_dir=$(mktemp -d)
gh release download v2.0.0 --repo beyondwin/skills --dir "$catalog_public_dir"
cp "$catalog_public_dir/korean-writing-editor-v2.0.0.zip" "$catalog_input_dir/"
cp "$catalog_public_dir/image-workbench-v2.0.0.zip" "$catalog_input_dir/"
cp "$catalog_public_dir/SHA256SUMS" "$catalog_input_dir/"
python3 scripts/release.py check --catalog --input "$catalog_input_dir"
python3 scripts/release.py build --catalog --input "$catalog_input_dir" --output "$catalog_output_dir"
python3 scripts/release.py verify-download --catalog --input "$catalog_output_dir"
python3 - "$catalog_public_dir/beyondwin-skills-v2.0.0.zip" "$catalog_output_dir/beyondwin-skills-v2.0.0.zip" <<'PY'
import sys
import zipfile
from pathlib import Path


def normalized_payload(path: str) -> list[tuple[str, int, bytes]]:
    with zipfile.ZipFile(Path(path)) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if len(names) != len(set(names)):
            raise SystemExit(f"duplicate ZIP member in {path}")
        return sorted(
            (
                member.filename,
                (member.external_attr >> 16) & 0o777,
                archive.read(member),
            )
            for member in members
            if not member.is_dir()
        )


if normalized_payload(sys.argv[1]) != normalized_payload(sys.argv[2]):
    raise SystemExit("rebuilt catalog payload differs from public v2.0.0")
PY
```

Expected: all commands PASS and the rebuilt two-skill `beyondwin-skills-v2.0.0.zip` has the same paths, normalized modes, and file bytes as the downloaded public plugin ZIP. Do not require compressed bytes to match across zlib versions.

- [ ] **Step 7: Commit locked catalog assembly**

```bash
git add scripts/catalog_contract.py scripts/release.py scripts/verify.py tests/contract/test_catalog_release.py tests/contract/test_verify.py
git commit -m "feat: assemble catalog from locked skill releases"
```

---

### Task 8: Rebuild the public documentation information architecture

**Files:**
- Rewrite: `README.md`
- Rewrite: `README.en.md`
- Create: `skills/korean-writing-editor/README.md`
- Create: `skills/korean-writing-editor/README.en.md`
- Create: `skills/image-workbench/README.md`
- Create: `skills/image-workbench/README.en.md`
- Create: `skills/graspic/README.md`
- Create: `skills/graspic/README.en.md`
- Create: `docs/users/ko/installation.md`
- Create: `docs/users/ko/compatibility.md`
- Create: `docs/users/ko/safety-and-privacy.md`
- Create: `docs/users/ko/verification.md`
- Create: `docs/users/en/installation.md`
- Create: `docs/users/en/compatibility.md`
- Create: `docs/users/en/safety-and-privacy.md`
- Create: `docs/users/en/verification.md`
- Replace with redirect stubs: `docs/ko/*.md`, `docs/en/*.md`
- Modify: `scripts/release_contract.py`
- Modify: `scripts/verify.py`
- Modify: `tests/contract/test_release_contract.py`
- Modify: `tests/contract/test_repository.py`
- Rewrite: `tests/contract/test_public_docs.py`
- Modify: `tests/contract/test_verify.py`

**Interfaces:**
- Consumes: product README links and shared support/safety facts.
- Produces: a two-click user path from root catalog to product install and invocation.

- [ ] **Step 1: Replace literal-version tests with ownership and reachability tests**

Add assertions that every product owns a Korean/English README pair, `validate_product` rejects a missing half of the pair, root/product READMEs contain no current version literal, every product is linked from root, shared user docs link back to all product READMEs, all active user-document links and anchors resolve, no user document is orphaned from the root catalog, and old paths contain only a language-appropriate relocation notice plus the new relative link. Update catalog stage expectations so `public-docs` runs after `catalog-release-contract` and before `python-compile`.

```python
def test_root_readmes_do_not_own_product_versions(self) -> None:
    for path in (ROOT / "README.md", ROOT / "README.en.md"):
        text = path.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\b[0-9]+\.[0-9]+\.[0-9]+\b")

def test_every_product_is_reachable_in_one_link_from_root(self) -> None:
    korean = (ROOT / "README.md").read_text(encoding="utf-8")
    english = (ROOT / "README.en.md").read_text(encoding="utf-8")
    for name in PRODUCT_NAMES:
        self.assertIn(f"skills/{name}/README.md", korean)
        self.assertIn(f"skills/{name}/README.en.md", english)
```

- [ ] **Step 2: Run public-doc tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_public_docs
```

Expected: FAIL on literal versions, old paths, and missing product links.

- [ ] **Step 3: Create the Korean and English product entry documents**

Every Korean README uses this exact heading order:

```markdown
# Korean Writing Editor
## 이 스킬이 해결하는 문제
## 사용해야 할 때와 사용하지 말아야 할 때
## 1분 설치와 첫 호출
## 주요 흐름
## 안전과 개인정보
## 호환성과 검증 수준
## 갱신과 버전 확인
## 변경 이력과 관리자 문서
```

Use titles `Image Workbench` and `graspic` with the same section order in their files. Include the exact matching installer command:

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

Include each product's existing invocation, support sentence, safety boundary, update check, CHANGELOG link, and its current flat maintainer-document link. Do not put a current numeric version in README prose. English files carry the same commands and public facts without maintainer-operation translations. Change `validate_product` so both files are now required. Task 9 replaces the temporary flat maintainer links with the final product directories.

- [ ] **Step 4: Rewrite root READMEs as short catalog entry points**

Keep the badges, one-sentence repository description, three-row selection table, individual install links, provider-free verify command, safety summary, and community links. Remove product contract detail, repeated version facts, long update/uninstall instructions, and repeated evidence explanations. Link each row directly to its product README.

- [ ] **Step 5: Create the paired shared user guides**

Use the exact Korean and English file pairs listed above. Installation owns shared installer/update/uninstall safety; compatibility owns the three exact support sentences; safety/privacy owns telemetry, user text, images, rights, and high-stakes boundaries; verification owns offline/live evidence and the two verify profiles. Do not copy detailed product modes from product READMEs.

- [ ] **Step 6: Replace old paths with one-minor relocation stubs**

Each Korean stub contains its new link and this sentence:

```markdown
이 문서는 독립 제품 문서 구조로 이동했습니다. 한 카탈로그 minor 동안 이 안내를 유지합니다.
```

Each English stub contains its new link and:

```markdown
This guide moved to the independent product documentation structure. This pointer remains for one catalog minor.
```

- [ ] **Step 7: Run link, parity, and claim tests**

```bash
python3 -m unittest tests.contract.test_public_docs
python3 scripts/verify.py --catalog
git diff --check
```

Expected: PASS with no stale two-skill or shared-version claim outside historical changelogs.

- [ ] **Step 8: Commit the public documentation architecture**

```bash
git add README.md README.en.md skills/korean-writing-editor/README.md skills/korean-writing-editor/README.en.md skills/image-workbench/README.md skills/image-workbench/README.en.md skills/graspic/README.md skills/graspic/README.en.md docs/users docs/ko docs/en scripts/release_contract.py scripts/verify.py tests/contract/test_release_contract.py tests/contract/test_repository.py tests/contract/test_public_docs.py tests/contract/test_verify.py
git commit -m "docs: organize public guides by product ownership"
```

---

### Task 9: Rebuild maintainer documentation and community routing

**Files:**
- Create: `docs/maintainers/README.md`
- Create: `docs/maintainers/repository/architecture.md`
- Create: `docs/maintainers/repository/versioning.md`
- Create: `docs/maintainers/repository/catalog-release.md`
- Move: `docs/maintainers/archive-migration.md` to `docs/maintainers/repository/archive-migration.md`
- Move: `docs/maintainers/archive-source-manifest.json` to `docs/maintainers/repository/archive-source-manifest.json`
- Create: `docs/maintainers/korean-writing-editor/{contract,testing,release}.md`
- Create: `docs/maintainers/image-workbench/{contract,testing,release}.md`
- Create: `docs/maintainers/graspic/{contract,testing,release}.md`
- Delete after content migration: `docs/maintainers/architecture.md`
- Delete after content migration: `docs/maintainers/release-process.md`
- Delete after content migration: `docs/maintainers/korean-writing-editor.md`
- Delete after content migration: `docs/maintainers/image-workbench.md`
- Delete after content migration: `docs/maintainers/graspic.md`
- Modify: `skills/korean-writing-editor/README.md`
- Modify: `skills/korean-writing-editor/README.en.md`
- Modify: `skills/image-workbench/README.md`
- Modify: `skills/image-workbench/README.en.md`
- Modify: `skills/graspic/README.md`
- Modify: `skills/graspic/README.en.md`
- Modify: `NOTICE`
- Modify: `.github/ISSUE_TEMPLATE/bug.yml`
- Modify: `.github/ISSUE_TEMPLATE/documentation.yml`
- Modify: `.github/pull_request_template.md`
- Modify: `tests/contract/test_public_docs.py`
- Modify: `tests/contract/test_community_and_ci.py`
- Modify: `tests/contract/test_archive_manifest.py`
- Modify: `tests/contract/test_repository.py`

**Interfaces:**
- Consumes: the source-of-truth matrix and product verification/release commands.
- Produces: one Korean maintainer map and exact change protocols per product.

- [ ] **Step 1: Write failing structure and stale-routing tests**

Require every product to have `contract.md`, `testing.md`, and `release.md`; require the repository trio and Archive evidence under `repository/`; require every maintainer document to be reachable from `docs/maintainers/README.md`; require both issue dropdowns to list all three products; forbid `two curated skills`, `two skills only`, and obsolete maintainer paths outside history.

- [ ] **Step 2: Run maintainer/community tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_public_docs tests.contract.test_community_and_ci tests.contract.test_archive_manifest
```

Expected: FAIL on the old flat structure and stale issue templates.

- [ ] **Step 3: Create the maintainer map and repository documents**

`docs/maintainers/README.md` must answer where architecture, versioning, catalog release, Archive provenance, and each product protocol live. `repository/architecture.md` owns installed/development boundaries; `versioning.md` owns the full SemVer decision table; `catalog-release.md` owns lock adoption and remote-byte gates. Keep all administrator prose Korean-first.

- [ ] **Step 4: Split each product change protocol by responsibility**

For each product:

- `contract.md` maps triggers, defaults, outputs, safety, and files that change together.
- `testing.md` names deterministic fixtures, exact commands, and evidence limitations.
- `release.md` names version source, SemVer examples, check/build/download commands, and failure recovery.

Preserve every concrete warning from the current flat files, including Korean text privacy, image rights, graspic rung fixtures, optional live boundaries, and inspector path rules. Update graspic's visual guidance to the already-committed artifact-page contract; do not revert it to the old chat-only claim. Replace all six product README links to flat maintainer files with links to each product's new contract, testing, and release documents.

- [ ] **Step 5: Move Archive evidence and update every reference**

Use `apply_patch` to create the two new repository paths with identical bytes, update NOTICE/tests/docs links, then delete the old files. Do not regenerate or alter the manifest payload or digest.

- [ ] **Step 6: Fix community routing for all three products**

Add `graspic` to bug and documentation dropdowns and change all two-skill descriptions to three-product wording. Add a PR checklist item requiring a matching `release.toml`/SKILL version decision and product CHANGELOG entry for installed-payload changes.

- [ ] **Step 7: Run maintainer, community, and Archive tests**

```bash
python3 -m unittest tests.contract.test_public_docs
python3 -m unittest tests.contract.test_community_and_ci
python3 -m unittest tests.contract.test_archive_manifest
python3 scripts/verify.py
```

Expected: all PASS.

- [ ] **Step 8: Commit maintainer and community restructuring**

```bash
git add docs/maintainers NOTICE .github skills/korean-writing-editor/README.md skills/korean-writing-editor/README.en.md skills/image-workbench/README.md skills/image-workbench/README.en.md skills/graspic/README.md skills/graspic/README.en.md tests/contract/test_public_docs.py tests/contract/test_community_and_ci.py tests/contract/test_archive_manifest.py tests/contract/test_repository.py
git commit -m "docs: define product maintainer ownership"
```

---

### Task 10: Target PR CI without weakening main verification

**Files:**
- Create: `scripts/changed_targets.py`
- Create: `tests/contract/test_changed_targets.py`
- Modify: `.github/workflows/verify.yml`
- Modify: `tests/contract/test_community_and_ci.py`

**Interfaces:**
- Consumes: a Git base revision and head revision or an explicit list of changed POSIX paths.
- Produces: deterministic GitHub Actions matrix JSON containing `target`, `os`, `profile`, and `selector`.

- [ ] **Step 1: Write failing target-mapping tests**

```python
def test_product_path_selects_only_that_product(self) -> None:
    self.assertEqual(targets_for_paths(["skills/graspic/SKILL.md"]), ("graspic",))

def test_shared_release_code_selects_every_target(self) -> None:
    self.assertEqual(
        targets_for_paths(["scripts/release_archive.py"]),
        ("catalog", "graspic", "image-workbench", "korean-writing-editor"),
    )

def test_unknown_path_fails_safe_to_every_target(self) -> None:
    self.assertEqual(
        targets_for_paths(["unexpected/new-surface.txt"]),
        ("catalog", "graspic", "image-workbench", "korean-writing-editor"),
    )
```

Also test product docs/tests, catalog files, shared public docs, LICENSE/NOTICE, empty diff, Windows rows, deterministic ordering, and JSON serialization.

- [ ] **Step 2: Run mapping tests and confirm RED**

```bash
python3 -m unittest tests.contract.test_changed_targets
```

Expected: ERROR because `scripts.changed_targets` does not exist.

- [ ] **Step 3: Implement fail-closed path routing**

Implement fail-closed routing with this core shape:

```python
TARGETS = ("catalog", "graspic", "image-workbench", "korean-writing-editor")
PRODUCT_PREFIXES = {
    "graspic": ("skills/graspic/", "tests/graspic/", "docs/maintainers/graspic/"),
    "image-workbench": ("skills/image-workbench/", "tests/image-workbench/", "docs/maintainers/image-workbench/"),
    "korean-writing-editor": ("skills/korean-writing-editor/", "tests/korean-writing-editor/", "docs/maintainers/korean-writing-editor/"),
}
PRODUCT_EXACT_PATHS = {
    "graspic": ("tests/contract/test_graspic.py",),
    "image-workbench": (),
    "korean-writing-editor": ("tests/contract/test_korean_package.py",),
}


def targets_for_paths(paths: Iterable[str]) -> Sequence[str]:
    normalized = tuple(sorted({path.replace("\\", "/") for path in paths}))
    if not normalized:
        return TARGETS
    selected: set[str] = set()
    for path in normalized:
        matched = False
        for target, prefixes in PRODUCT_PREFIXES.items():
            if path.startswith(prefixes) or path in PRODUCT_EXACT_PATHS[target]:
                selected.add(target)
                matched = True
        if path.startswith("catalog/"):
            selected.add("catalog")
            matched = True
        if not matched:
            return TARGETS
    return tuple(sorted(selected))
```

Add `matrix_for_targets(targets: Iterable[str]) -> dict[str, list[dict[str, str]]]` and `changed_paths(root: Path, base: str, head: str) -> Sequence[str]`. Product-owned paths select that product. `catalog/` selects catalog. Shared scripts, contract tests, root docs, LICENSE, NOTICE, workflow files, or an unknown path select every target. An empty diff also selects every target.

- [ ] **Step 4: Update the workflow with a detect job and dynamic matrix**

Use `actions/checkout` with `fetch-depth: 0`. On pull requests, call `changed_targets.py` with the event's base and head SHA and write canonical compact JSON to `$GITHUB_OUTPUT`. On pushes to main and manual dispatch, return the existing three full rows. Each PR target must run on Ubuntu and macOS with `full`; Windows uses `windows-portable`. Matrix selectors must be fixed strings produced by the script: `--catalog`, `--skill graspic`, `--skill image-workbench`, or `--skill korean-writing-editor`.

- [ ] **Step 5: Add workflow contract assertions**

Require `fetch-depth: 0`, the detect job, `fromJSON`, all current OS/profile coverage, `permissions: contents: read`, no secrets, and no provider/live flags.

- [ ] **Step 6: Run mapping and workflow tests**

```bash
python3 -m unittest tests.contract.test_changed_targets
python3 -m unittest tests.contract.test_community_and_ci
python3 scripts/verify.py
```

Expected: PASS.

- [ ] **Step 7: Commit targeted CI**

```bash
git add scripts/changed_targets.py tests/contract/test_changed_targets.py .github/workflows/verify.yml tests/contract/test_community_and_ci.py
git commit -m "ci: verify changed skill products independently"
```

---

### Task 11: Close the migration with end-to-end local evidence

**Files:**
- Modify: `docs/superpowers/specs/2026-08-27-independent-skill-product-architecture-design.md`
- Modify: `docs/superpowers/plans/2026-08-27-independent-skill-product-architecture.md` only to mark completed checkboxes during execution

**Interfaces:**
- Consumes: all product, catalog, documentation, release, and CI contracts.
- Produces: a clean locally verified branch ready for separate release authorization.

- [x] **Step 1: Run placeholder, stale-fact, and tree checks**

```bash
rg -n '\b(T[B]D|T[O]DO|F[I]XME|X[X]X)\b' README.md README.en.md skills catalog docs/users docs/maintainers docs/ko docs/en .github scripts tests
rg -n 'exactly two skills|two curated skills|two skills only' README.md README.en.md skills catalog/README.md docs/users docs/maintainers docs/ko docs/en .github
find skills catalog docs/maintainers docs/users -maxdepth 3 -type f | sort
git diff --check
```

Expected: no placeholder or stale-current claim in active documentation and code. Historical changelogs and superseded design/plan records under `docs/superpowers/` may describe the legacy two-skill `v2.0.0` only with an explicit historical scope.

- [x] **Step 2: Run every independent verifier**

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py --skill image-workbench
python3 scripts/verify.py --skill graspic
python3 scripts/verify.py --catalog
```

Expected: all PASS.

- [x] **Step 3: Run the complete cross-platform-local profile set**

```bash
python3 scripts/verify.py --profile full
python3 scripts/verify.py --profile windows-portable
python3 -m compileall -q scripts tests skills
```

Expected: all PASS without credentials, providers, models, or remote images.

- [x] **Step 4: Exercise legacy catalog reconstruction from public bytes**

```bash
final_public_dir=$(mktemp -d)
final_catalog_input=$(mktemp -d)
final_catalog_output=$(mktemp -d)
gh release download v2.0.0 --repo beyondwin/skills --dir "$final_public_dir"
cp "$final_public_dir/korean-writing-editor-v2.0.0.zip" "$final_catalog_input/"
cp "$final_public_dir/image-workbench-v2.0.0.zip" "$final_catalog_input/"
cp "$final_public_dir/SHA256SUMS" "$final_catalog_input/"
python3 scripts/release.py check --catalog --input "$final_catalog_input"
python3 scripts/release.py build --catalog --input "$final_catalog_input" --output "$final_catalog_output"
python3 scripts/release.py verify-download --catalog --input "$final_catalog_output"
python3 - "$final_public_dir/beyondwin-skills-v2.0.0.zip" "$final_catalog_output/beyondwin-skills-v2.0.0.zip" <<'PY'
import sys
import zipfile
from pathlib import Path


def normalized_payload(path: str) -> list[tuple[str, int, bytes]]:
    with zipfile.ZipFile(Path(path)) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if len(names) != len(set(names)):
            raise SystemExit(f"duplicate ZIP member in {path}")
        return sorted(
            (
                member.filename,
                (member.external_attr >> 16) & 0o777,
                archive.read(member),
            )
            for member in members
            if not member.is_dir()
        )


if normalized_payload(sys.argv[1]) != normalized_payload(sys.argv[2]):
    raise SystemExit("rebuilt catalog payload differs from public v2.0.0")
PY
```

Expected: all PASS and normalized public/rebuilt catalog payloads are equal. Report compressed-byte equality only if separately observed.

- [x] **Step 5: Confirm product release readiness remains honest**

```bash
python3 scripts/release.py check --product korean-writing-editor
python3 scripts/release.py check --product image-workbench
python3 scripts/release.py check --product graspic
git tag --list 'korean-writing-editor-v*' 'image-workbench-v*' 'graspic-v*' 'beyondwin-skills-v*'
```

Expected: checks PASS in development mode, no new product-qualified tags exist, and no public-release claim has been added.

- [x] **Step 6: Mark the design locally implemented and release pending**

Change the spec status line to:

```markdown
- 상태: 로컬 구현 및 provider-free 검증 완료, 독립 공개 릴리스 승인 대기
```

Do not change the migration target versions or claim GitHub publication.

- [x] **Step 7: Commit the final verified state**

```bash
git add docs/superpowers/specs/2026-08-27-independent-skill-product-architecture-design.md docs/superpowers/plans/2026-08-27-independent-skill-product-architecture.md
git commit -m "docs: record independent skill migration verification"
```

- [x] **Step 8: Review the branch without publishing it**

```bash
git status --short --branch --untracked-files=all
git log --oneline --decorate origin/main..HEAD
git diff --stat origin/main..HEAD
```

Expected: clean tree, only planned commits, no generated archives/evidence, no tags, no push, and no GitHub Release creation.

---

## New-Session Execution Prompt

```text
Use $superpowers:subagent-driven-development to execute the implementation plan at docs/superpowers/plans/2026-08-27-independent-skill-product-architecture.md. Read that plan and docs/superpowers/specs/2026-08-27-independent-skill-product-architecture-design.md completely before acting. Use $superpowers:using-git-worktrees to create an isolated worktree and feature branch from the current branch HEAD; commits 4be206f and 8ee8c01 must remain in its ancestry. Initialize this plan's SDD workspace and ledger, perform the required cross-task preflight table, and record autonomous rulings there before Task 1.

Execute every task in order with a fresh implementation subagent. After each task, require one independent task reviewer to return both spec-compliance and task-quality verdicts; run the skill's bounded fix/re-review loop for every blocking finding. After all tasks, run the broad whole-branch review on the most capable available model. Follow RED -> GREEN -> refactor, run the exact verification commands, and commit at every task boundary. Specify the model on every subagent dispatch according to the skill's model-selection rules. When routine in-scope defects, test failures, documentation drift, platform issues, or design ambiguities appear, investigate evidence, add regression coverage, make and ledger the safest spec-consistent ruling, and continue without asking me. Do not stop until every local task and all provider-free verification gates pass.

Preserve unrelated work and do not reset, clean, overwrite, or delete broad paths. Do not push, merge into a shared branch, create or move tags, publish GitHub Releases, mutate Archive, call live providers, or make any other external write; those actions require separate authority and are outside this plan. Stop only for an irreversible or destructive operation, a security-sensitive action, a side effect outside the isolated worktree that normally requires approval, or a plan defect so fundamental that every remaining path is a guess. Report exact files, commits, verification commands and results, all ledger rulings with their cost if wrong, and any remaining release-only gate at the end.
```

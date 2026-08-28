# Repository Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the repository around one validated product registry, mirrored product/test/maintainer paths, focused reusable tooling, and clearly separated current versus historical documentation while keeping all three current products green under their existing identities.

**Architecture:** `products.toml` becomes the only ordered index of current products, supported hosts, owned paths, and verification stage identifiers; each product's `release.toml` remains the only version source. Reusable Python contracts move to `scripts/lib/`, while CLI entry points load the registry and invoke registered code. Product tests and maintainer docs mirror each registered child of `skills/`; repository-wide contracts live under `tests/repository/`; the immutable v2.0.0 catalog remains independent of the registry.

**Tech Stack:** Python 3.11+ standard library (`argparse`, `dataclasses`, `pathlib`, `tomllib`, `unittest`), TOML, Markdown, GitHub Actions, Git.

**Spec:** `docs/superpowers/specs/2026-08-28-how-it-works-repository-architecture-design.md` (moved by Task 8 to `docs/history/specs/2026-08-28-how-it-works-repository-architecture-design.md`)

## Global Constraints

- Keep the product identities `korean-writing-editor`, `image-workbench`, and `graspic` unchanged throughout this plan; the rename belongs to the dependent How It Works plan.
- Keep every registered child of `skills/` directly installable and free of tests, maintainer documents, live evidence, and repository tooling.
- `products.toml` owns ordered discovery, display names, supported-host claims, owned paths, and verification stage identifiers; it never owns versions or shell commands.
- Each product's `release.toml` under `skills/` remains the only version and tag source.
- `catalog/` and its v2.0.0 legacy fixtures remain immutable and are never populated from `products.toml`.
- Unregistered product/test/doc directories, duplicate names or paths, unknown hosts or stages, and identity mismatches fail closed.
- Unmatched changed paths select the full repository matrix; normalize `\\` to `/` before routing.
- Provider-free CI must not call models, require credentials, or run optional live smoke.
- Preserve unrelated user changes. Do not publish, tag, push, create a GitHub Release, or edit local host skill links in this plan.
- Use Git-aware moves. Do not rewrite historical prose merely to make it current.
- Run Python with `PYTHONDONTWRITEBYTECODE=1` during verification so no new bytecode residue is created.

---

## Locked File Map

The end state of this plan is:

```text
products.toml                              current product index; no versions or commands
scripts/lib/product_registry.py            registry types, parser, validation, path normalization
scripts/lib/product_contract.py            payload/frontmatter/release.toml validation
scripts/lib/verification.py                 registered Stage implementations and profile selection
scripts/lib/change_routing.py               registry-driven changed-path target selection and matrices
scripts/lib/archive.py                      deterministic ZIP, checksum, extraction, archive safety
scripts/lib/catalog.py                      immutable catalog lock and catalog validation
scripts/lib/archive_manifest.py             Archive migration capture/verification logic
scripts/lib/documentation.py                Markdown links and registry-derived public facts
scripts/verify.py                           thin verification CLI
scripts/release.py                          product/catalog check-build-verify-download CLI
scripts/changed_targets.py                  thin GitHub Actions matrix CLI
scripts/capture_archive_manifest.py         thin archive-manifest CLI
tests/products/korean-writing-editor/       Korean editor fixtures, runners, and contracts
tests/products/image-workbench/             image workbench fixtures, runner, and contracts
tests/products/graspic/                     explanation fixtures and contracts
tests/repository/                           registry, release, docs, catalog, archive, CI contracts
docs/README.md                              reader router
docs/users/{ko,en}/                         four current paired user guides
docs/maintainers/products/korean-writing-editor/  Korean editor maintainer guides
docs/maintainers/products/image-workbench/        image workbench maintainer guides
docs/maintainers/products/graspic/                explanation maintainer guides
docs/maintainers/repository/                architecture/registry/version/release/catalog/migration guides
docs/history/{README.md,specs/,plans/}      non-authoritative point-in-time records
catalog/                                    unchanged v2.0.0 reproduction boundary
```

The public interfaces shared across tasks are:

```python
@dataclasses.dataclass(frozen=True)
class Product:
    name: str
    display_name: str
    skill_path: pathlib.PurePosixPath
    test_path: pathlib.PurePosixPath
    maintainer_docs: pathlib.PurePosixPath
    supported_hosts: tuple[str, ...]
    owned_paths: tuple[pathlib.PurePosixPath, ...]
    verify_stages: tuple[str, ...]

@dataclasses.dataclass(frozen=True)
class ProductRegistry:
    schema_version: int
    products: tuple[Product, ...]

    @property
    def names(self) -> tuple[str, ...]: ...
    def require(self, name: str) -> Product: ...

def load_registry(path: pathlib.Path) -> ProductRegistry: ...
def validate_registry(
    root: pathlib.Path,
    registry: ProductRegistry,
    registered_stages: collections.abc.Collection[str],
) -> list[str]: ...
def normalize_repo_path(value: str | pathlib.PurePath) -> str: ...

def active_markdown_paths(root: pathlib.Path) -> tuple[pathlib.Path, ...]: ...
def markdown_links(path: pathlib.Path) -> tuple[str, ...]: ...
def broken_markdown_links(
    root: pathlib.Path,
    paths: collections.abc.Iterable[pathlib.Path],
) -> list[str]: ...
```

### Task 1: Add the product registry parser and schema contract

**Files:**
- Create: `products.toml`
- Create: `scripts/lib/__init__.py`
- Create: `scripts/lib/product_registry.py`
- Create: `tests/repository/test_product_registry.py`

**Interfaces:**
- Consumes: existing `skills/*/release.toml`, `SKILL.md`, test paths, and maintainer-doc paths without modifying them.
- Produces: `Product`, `ProductRegistry`, `load_registry(path)`, `validate_registry(root, registry, registered_stages)`, and `normalize_repo_path(value)` exactly as declared in the locked file map.

- [ ] **Step 1: Write parser tests before adding the registry**

```python
class RegistryParsingTests(unittest.TestCase):
    def test_repository_registry_preserves_product_order(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(
            registry.names,
            ("korean-writing-editor", "image-workbench", "graspic"),
        )

    def test_registry_contains_no_version_or_command_fields(self) -> None:
        raw = tomllib.loads((ROOT / "products.toml").read_text(encoding="utf-8"))
        for product in raw["products"]:
            self.assertNotIn("version", product)
            self.assertNotIn("tag_prefix", product)
            self.assertNotIn("command", product)

    def test_windows_paths_are_normalized(self) -> None:
        self.assertEqual(
            normalize_repo_path(r"tests\\products\\graspic\\cases.json"),
            "tests/products/graspic/cases.json",
        )
```

- [ ] **Step 2: Run the focused test and confirm the missing-module failure**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry -v`

Expected: FAIL because `scripts.lib.product_registry` and `products.toml` do not exist.

- [ ] **Step 3: Add the current-name registry**

Use the paths that exist at this task boundary. Task 3 changes only the
`test_path`, `maintainer_docs`, and matching `owned_paths` values when it moves
those trees into their final mirrored locations; this keeps registry validation
green between tasks.

```toml
schema_version = 1

[[products]]
name = "korean-writing-editor"
display_name = "Korean Writing Editor"
skill_path = "skills/korean-writing-editor"
test_path = "tests/korean-writing-editor"
maintainer_docs = "docs/maintainers/korean-writing-editor"
supported_hosts = ["codex"]
owned_paths = [
  "skills/korean-writing-editor/",
  "tests/korean-writing-editor/",
  "docs/maintainers/korean-writing-editor/",
]
verify_stages = [
  "product-contract",
  "korean-package",
  "korean-offline",
  "korean-live-unit",
  "korean-live-dry-run",
  "python-compile",
]

[[products]]
name = "image-workbench"
display_name = "Image Workbench"
skill_path = "skills/image-workbench"
test_path = "tests/image-workbench"
maintainer_docs = "docs/maintainers/image-workbench"
supported_hosts = ["codex"]
owned_paths = [
  "skills/image-workbench/",
  "tests/image-workbench/",
  "docs/maintainers/image-workbench/",
]
verify_stages = ["product-contract", "image-contract", "image-inspector", "python-compile"]

[[products]]
name = "graspic"
display_name = "graspic"
skill_path = "skills/graspic"
test_path = "tests/graspic"
maintainer_docs = "docs/maintainers/graspic"
supported_hosts = ["codex"]
owned_paths = [
  "skills/graspic/",
  "tests/graspic/",
  "docs/maintainers/graspic/",
]
verify_stages = ["product-contract", "graspic-contract", "python-compile"]
```

- [ ] **Step 4: Implement strict TOML parsing**

Implement the declared frozen dataclasses. `load_registry()` must reject non-schema-1 data, missing or extra product keys, non-string list items, absolute paths, `..` segments, paths without the required trailing directory relationship, and malformed product names that do not match `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Use `ValueError` messages that name the field and product.

```python
KNOWN_HOSTS = frozenset({"codex", "claude-code", "grok", "cursor"})
PRODUCT_KEYS = frozenset({
    "name", "display_name", "skill_path", "test_path", "maintainer_docs",
    "supported_hosts", "owned_paths", "verify_stages",
})

def normalize_repo_path(value: str | pathlib.PurePath) -> str:
    return str(value).replace("\\", "/").lstrip("./")
```

- [ ] **Step 5: Run parser tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry.RegistryParsingTests -v`

Expected: PASS.

- [ ] **Step 6: Add malformed-registry table tests**

Cover duplicate product names, duplicate `skill_path`, duplicate owned paths, unknown hosts, absolute paths, parent traversal, wrong types, extra keys, and missing keys using a temporary TOML file. Assert stable message fragments such as `duplicate product name`, `unknown host`, and `path must be repository-relative`.

- [ ] **Step 7: Run the complete registry test module**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry -v`

Expected: PASS for parser tests; directory coverage tests are not added until Task 3 creates the target tree.

- [ ] **Step 8: Commit the parser and registry**

```bash
git add products.toml scripts/lib/__init__.py scripts/lib/product_registry.py tests/repository/test_product_registry.py
git commit -m "feat: add repository product registry"
```

### Task 2: Make product validation consume the registry

**Files:**
- Move: `scripts/release_contract.py` -> `scripts/lib/product_contract.py`
- Modify: `scripts/lib/product_contract.py`
- Modify: `scripts/release.py`
- Modify: `scripts/catalog_contract.py`
- Modify: `scripts/catalog_lock.py`
- Modify: `tests/contract/test_release_contract.py`
- Modify: `tests/contract/test_public_docs.py`
- Modify: `tests/contract/test_repository.py`

**Interfaces:**
- Consumes: `ProductRegistry` and `load_registry(ROOT / "products.toml")` from Task 1.
- Produces: `validate_product(skill_root: Path, registry: ProductRegistry) -> list[str]` and `stage_product(skill_root: Path, destination: Path, registry: ProductRegistry) -> Path`; removes `PRODUCT_NAMES` as an authoritative tuple.

- [ ] **Step 1: Change contract tests to prove the registry is authoritative**

```python
def test_unregistered_skill_is_rejected(self) -> None:
    errors = validate_product(self.root / "skills" / "not-registered", self.registry)
    self.assertIn("unlisted skill is not accepted: not-registered", errors)

def test_registered_names_come_only_from_products_toml(self) -> None:
    source = (ROOT / "scripts/lib/product_contract.py").read_text(encoding="utf-8")
    self.assertNotIn("PRODUCT_NAMES =", source)
    self.assertEqual(self.registry.names, tuple(product.name for product in self.registry.products))
```

- [ ] **Step 2: Run the focused tests and confirm signature/import failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_release_contract tests.contract.test_repository -v`

Expected: FAIL because the module still lives at `scripts.release_contract` and `validate_product` does not accept a registry.

- [ ] **Step 3: Move the module and update its public signatures**

Use `git mv scripts/release_contract.py scripts/lib/product_contract.py`. Replace membership checks against `PRODUCT_NAMES` with `registry.names`. Pass the same registry through `stage_product`; leave payload hashing, frontmatter parsing, SemVer checks, link validation, and release metadata behavior unchanged.

- [ ] **Step 4: Update all direct callers and tests in one mechanical pass**

Replace imports of `scripts.release_contract` with `scripts.lib.product_contract`; create one module-level `REGISTRY = load_registry(ROOT / "products.toml")` only in CLI/test entry points; pass it explicitly to `validate_product()` and `stage_product()`. Do not add a compatibility re-export module.

- [ ] **Step 5: Run product/release contracts**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_release_contract tests.contract.test_repository tests.contract.test_release -v`

Expected: PASS.

- [ ] **Step 6: Run current product release checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product korean-writing-editor
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product graspic
```

Expected: all exit 0 and print no contract errors.

- [ ] **Step 7: Commit the registry-backed contract**

```bash
git add scripts/lib/product_contract.py scripts/release.py scripts/catalog_contract.py scripts/catalog_lock.py tests/contract
git commit -m "refactor: derive product validation from registry"
```

### Task 3: Mirror product tests and maintainer documents

**Files:**
- Move: `tests/korean-writing-editor/` -> `tests/products/korean-writing-editor/`
- Move: `tests/image-workbench/` -> `tests/products/image-workbench/`
- Move: `tests/graspic/` -> `tests/products/graspic/`
- Move: `tests/contract/test_korean_package.py` -> `tests/products/korean-writing-editor/test_package.py`
- Move: `tests/contract/test_graspic.py` -> `tests/products/graspic/test_contract.py`
- Move: `docs/maintainers/korean-writing-editor/` -> `docs/maintainers/products/korean-writing-editor/`
- Move: `docs/maintainers/image-workbench/` -> `docs/maintainers/products/image-workbench/`
- Move: `docs/maintainers/graspic/` -> `docs/maintainers/products/graspic/`
- Create: `docs/maintainers/products/korean-writing-editor/compatibility.md`
- Create: `docs/maintainers/products/image-workbench/compatibility.md`
- Create: `docs/maintainers/products/graspic/compatibility.md`
- Modify: path-bearing product tests, product READMEs, current user docs, maintainer docs, `scripts/verify.py`, and `tests/contract/test_verify.py`
- Modify: `tests/repository/test_product_registry.py`

**Interfaces:**
- Consumes: `Product.skill_path`, `test_path`, `maintainer_docs`, and `verify_stages`.
- Produces: one physical product test tree and one four-file maintainer-doc tree for every registry entry.

- [ ] **Step 1: Add directory-coverage tests**

```python
def test_registry_exactly_covers_product_directories(self) -> None:
    registry = load_registry(ROOT / "products.toml")
    self.assertEqual(
        {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
        set(registry.names),
    )
    self.assertEqual(
        {path.name for path in (ROOT / "tests/products").iterdir() if path.is_dir()},
        set(registry.names),
    )
    self.assertEqual(
        {path.name for path in (ROOT / "docs/maintainers/products").iterdir() if path.is_dir()},
        set(registry.names),
    )

def test_each_product_has_four_maintainer_guides(self) -> None:
    expected = {"contract.md", "testing.md", "compatibility.md", "release.md"}
    for product in self.registry.products:
        actual = {path.name for path in (ROOT / product.maintainer_docs).glob("*.md")}
        self.assertEqual(actual, expected, product.name)
```

- [ ] **Step 2: Run coverage tests and confirm missing-directory failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry -v`

Expected: FAIL because `tests/products/`, `docs/maintainers/products/`, and compatibility guides do not yet exist.

- [ ] **Step 3: Perform Git-aware directory moves without changing fixture bytes**

Use `git mv` for the five test moves and three maintainer-doc moves listed above. Move `tests/contract/fixtures/legacy-bundle-v2.0.0/` later with repository tests; do not move it under a current product because it belongs to the immutable catalog.

- [ ] **Step 4: Change registry paths to the mirrored destinations**

Set the three `test_path` values to
`tests/products/korean-writing-editor`, `tests/products/image-workbench`, and
`tests/products/graspic`. Set the three `maintainer_docs` values to the same
suffixes under `docs/maintainers/products/`, then replace the matching
`owned_paths` entries. Keep product order, host claims, and verification stage
identifiers unchanged.

- [ ] **Step 5: Update every active path reference**

Use `rg` to enumerate references, then use `apply_patch` to change:

```text
tests/korean-writing-editor/        -> tests/products/korean-writing-editor/
tests/image-workbench/              -> tests/products/image-workbench/
tests/graspic/                       -> tests/products/graspic/
tests/contract/test_korean_package  -> tests/products/korean-writing-editor/test_package.py or discovery path
tests/contract/test_graspic         -> tests/products/graspic/test_contract.py or discovery path
docs/maintainers/korean-writing-editor/ -> docs/maintainers/products/korean-writing-editor/
docs/maintainers/image-workbench/       -> docs/maintainers/products/image-workbench/
docs/maintainers/graspic/               -> docs/maintainers/products/graspic/
```

Update relative links from each product README from `../../docs/maintainers/...` to `../../docs/maintainers/products/...`. Keep all test data, synthetic prompts, and expected outputs byte-for-byte unless a path string itself is the subject of a test.

- [ ] **Step 6: Add the three compatibility guides**

Each Korean-first guide must state: current supported host from the registry (`codex`), required host capabilities, provider-free evidence, live-evidence boundary, and the rule that new support needs discovery/explicit/implicit-near-miss/output smoke. For `image-workbench`, retain the Codex image generation/local viewing dependency. Do not claim Claude Code, Grok, or Cursor support in this plan.

- [ ] **Step 7: Point temporary verification stages at the new paths**

In `scripts/verify.py`, change stage arguments to `tests/products/...` and the repository contract discovery path only where files already moved. In `tests/contract/test_verify.py`, assert the new paths. Do not yet refactor the hard-coded stage catalog; Task 5 removes it.

- [ ] **Step 8: Run all moved product tests directly**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/korean-writing-editor/offline/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/korean-writing-editor/live -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/korean-writing-editor/live/live_matrix.py --dry-run
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/graspic -p 'test_*.py'
```

Expected: all exit 0.

- [ ] **Step 9: Run registry and verification tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry tests.contract.test_verify -v`

Expected: PASS.

- [ ] **Step 10: Commit the mirrored product structure**

```bash
git add tests docs skills scripts/verify.py products.toml
git commit -m "refactor: mirror product tests and maintainer docs"
```

### Task 4: Move repository-wide tests under one boundary

**Files:**
- Move: `tests/contract/fixtures/` -> `tests/repository/fixtures/`
- Move: every remaining `tests/contract/test_*.py` -> `tests/repository/test_*.py`
- Modify: imports, `ROOT` depth calculations, fixture constants, subprocess module paths, `scripts/verify.py`

**Interfaces:**
- Consumes: all current repository contract test names and assertions.
- Produces: `python3 -m unittest discover -s tests/repository -p 'test_*.py'` as the single repository-contract command.

- [ ] **Step 1: Add a structure assertion before moving files**

Add to `test_repository.py`:

```python
def test_tests_have_only_product_and_repository_roots(self) -> None:
    roots = {path.name for path in (ROOT / "tests").iterdir() if path.is_dir() and path.name != "__pycache__"}
    self.assertEqual(roots, {"products", "repository"})
```

- [ ] **Step 2: Run it and confirm the old `contract` directory fails the assertion**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_repository.RepositoryContractTests.test_tests_have_only_product_and_repository_roots -v`

Expected: FAIL showing `contract` as an extra root.

- [ ] **Step 3: Move remaining tests and immutable fixtures with `git mv`**

Move the contents, not the enclosing directory over itself. Preserve legacy fixture bytes and paths below `tests/repository/fixtures/legacy-bundle-v2.0.0/`.

- [ ] **Step 4: Repair test roots and module paths**

Every moved top-level test continues to use `ROOT = Path(__file__).resolve().parents[2]`. Replace each `tests.contract` module prefix with `tests.repository`, `tests/contract/fixtures` with `tests/repository/fixtures`, and repository discovery with `tests/repository`. Use `rg -n 'tests/contract|tests\.contract' .` and leave no active matches.

- [ ] **Step 5: Run the repository suite**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'`

Expected: PASS.

- [ ] **Step 6: Run all three product selectors**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill korean-writing-editor
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill graspic
```

Expected: all exit 0.

- [ ] **Step 7: Commit repository test relocation**

```bash
git add tests scripts/verify.py
git commit -m "refactor: separate product and repository tests"
```

### Task 5: Register verification stages in code and select them from TOML

**Files:**
- Create: `scripts/lib/verification.py`
- Modify: `scripts/verify.py`
- Modify: `tests/repository/test_verify.py`
- Modify: `tests/repository/test_product_registry.py`

**Interfaces:**
- Consumes: `Product.verify_stages` and `validate_registry(..., REGISTERED_STAGE_NAMES)`.
- Produces: `Stage`, `REGISTERED_STAGES: Mapping[str, Stage]`, `REGISTERED_STAGE_NAMES`, `stages(root, profile, registry, skill=None, catalog=False) -> Sequence[Stage]`, and `run_stages(stage_list) -> int`.

- [ ] **Step 1: Add tests for registered-stage selection**

```python
def test_product_stage_order_comes_from_registry(self) -> None:
    product = self.registry.require("graspic")
    selected = stages(ROOT, "full", self.registry, skill="graspic")
    self.assertEqual(tuple(stage.name for stage in selected), product.verify_stages)

def test_unknown_registry_stage_fails_validation(self) -> None:
    broken = dataclasses.replace(
        self.registry,
        products=(dataclasses.replace(self.registry.products[0], verify_stages=("missing-stage",)),) + self.registry.products[1:],
    )
    self.assertIn("unknown verification stage: missing-stage", validate_registry(ROOT, broken, REGISTERED_STAGE_NAMES))
```

- [ ] **Step 2: Run focused tests and confirm missing-interface failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_verify tests.repository.test_product_registry -v`

Expected: FAIL because `scripts.lib.verification` is absent and selection is hard-coded.

- [ ] **Step 3: Move the stage implementation into `scripts/lib/verification.py`**

Keep the existing stage IDs and command order. Update paths to the new test tree. Define `REGISTERED_STAGES` from a `_stage_catalog(root)` function; define the accepted identifiers as `frozenset(_stage_catalog(ROOT))`. The full suite must use `repository-contract` plus product runner stages and `python-compile`; the catalog selector must keep `catalog-contract`, `catalog-release-contract`, `public-docs`, and `python-compile`. `windows-portable` continues to exclude only `image-contract` and `image-inspector`.

- [ ] **Step 4: Reduce `scripts/verify.py` to argument parsing and delegation**

```python
def main(argv: list[str] | None = None) -> int:
    registry = load_registry(ROOT / "products.toml")
    errors = validate_registry(ROOT, registry, REGISTERED_STAGE_NAMES)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    parser = build_parser(registry.names)
    args = parser.parse_args(argv)
    return run_stages(stages(ROOT, args.profile, registry, skill=args.skill, catalog=args.catalog))
```

- [ ] **Step 5: Run verification unit tests and full provider-free verification**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_verify tests.repository.test_product_registry -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: all exit 0; full verification prints each registered stage once in deterministic order.

- [ ] **Step 6: Commit the stage registry**

```bash
git add scripts/verify.py scripts/lib/verification.py tests/repository/test_verify.py tests/repository/test_product_registry.py
git commit -m "refactor: select verification stages from product registry"
```

### Task 6: Drive changed-target routing from owned paths

**Files:**
- Create: `scripts/lib/change_routing.py`
- Modify: `scripts/changed_targets.py`
- Modify: `tests/repository/test_changed_targets.py`
- Modify: `tests/repository/test_community_and_ci.py`
- Modify: `.github/workflows/verify.yml` only if the existing CLI contract requires a path update

**Interfaces:**
- Consumes: ordered `ProductRegistry.products`, each `owned_paths`, and `normalize_repo_path()`.
- Produces: `targets_for_paths(paths, registry)`, `matrix_for_targets(targets, registry)`, `full_repository_matrix()`, `matrix_for_event(event, root, registry, base="", head="")`, and JSON serialization; `scripts/changed_targets.py` keeps its current CLI arguments.

- [ ] **Step 1: Replace hard-coded routing assertions with registry-driven cases**

```python
def test_each_owned_path_routes_to_its_product(self) -> None:
    for product in self.registry.products:
        for prefix in product.owned_paths:
            changed = f"{prefix.as_posix().rstrip('/')}/probe.txt"
            self.assertEqual(targets_for_paths([changed], self.registry), (product.name,))

def test_windows_separator_routes_to_product(self) -> None:
    self.assertEqual(
        targets_for_paths([r"tests\\products\\graspic\\cases.json"], self.registry),
        ("graspic",),
    )

def test_unmatched_path_selects_full_matrix(self) -> None:
    self.assertEqual(targets_for_paths(["products.toml"], self.registry), ("catalog", *self.registry.names))
```

- [ ] **Step 2: Run routing tests and confirm signature failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_changed_targets -v`

Expected: FAIL because current functions have no registry parameter and use old path constants.

- [ ] **Step 3: Implement registry-driven routing**

Treat `catalog/` as the only narrow catalog prefix. For each normalized path, collect every matching product owner. If any path matches nothing, return all targets in deterministic order `("catalog", *registry.names)`. Repository-wide paths including `products.toml`, `scripts/`, `.github/`, shared docs, root files, and `tests/repository/` therefore fail closed to full verification.

- [ ] **Step 4: Make `scripts/changed_targets.py` a thin CLI wrapper**

It loads and validates the registry, delegates to `scripts.lib.change_routing`, writes `matrix=` followed by canonical JSON to GitHub output, and returns nonzero on registry errors. Preserve push/workflow_dispatch full-matrix behavior and pull-request diff behavior.

- [ ] **Step 5: Run routing, workflow, and real CLI tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_changed_targets tests.repository.test_community_and_ci -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/changed_targets.py --event workflow_dispatch
```

Expected: tests PASS; CLI emits one valid JSON matrix with Ubuntu, macOS, and Windows rows.

- [ ] **Step 6: Commit change routing**

```bash
git add scripts/changed_targets.py scripts/lib/change_routing.py tests/repository/test_changed_targets.py tests/repository/test_community_and_ci.py .github/workflows/verify.yml
git commit -m "refactor: route changed products from registry"
```

### Task 7: Consolidate reusable release, catalog, and archive code

**Files:**
- Move: `scripts/release_archive.py` -> `scripts/lib/archive.py`
- Move: `scripts/catalog_contract.py` -> `scripts/lib/catalog.py`
- Create: `scripts/lib/archive_manifest.py` from the reusable portion of `scripts/capture_archive_manifest.py`
- Modify: `scripts/capture_archive_manifest.py` into a thin CLI
- Modify: `scripts/release.py`, `scripts/catalog_lock.py`, `scripts/build_release.py`
- Modify: `tests/repository/test_release.py`, `test_catalog_contract.py`, `test_catalog_release.py`, `test_archive_manifest.py`

**Interfaces:**
- Consumes: registry-backed `scripts.lib.product_contract` and all current deterministic archive/catalog behavior.
- Produces: importable `scripts.lib.archive`, `scripts.lib.catalog`, and `scripts.lib.archive_manifest`; no top-level module remains as a second implementation.

- [ ] **Step 1: Add a tooling-boundary test**

```python
def test_reusable_tooling_lives_under_scripts_lib(self) -> None:
    forbidden = {
        "release_contract.py", "release_archive.py", "catalog_contract.py",
    }
    self.assertTrue(forbidden.isdisjoint({path.name for path in (ROOT / "scripts").glob("*.py")}))
    for name in ("product_registry.py", "product_contract.py", "verification.py", "change_routing.py", "archive.py", "catalog.py", "archive_manifest.py"):
        self.assertTrue((ROOT / "scripts/lib" / name).is_file(), name)
```

- [ ] **Step 2: Run it and confirm old top-level modules fail the boundary**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_repository -v`

Expected: FAIL listing `release_archive.py` and `catalog_contract.py` or the missing new modules.

- [ ] **Step 3: Move archive and catalog modules with no behavior edits**

Use `git mv`, then update imports everywhere to `scripts.lib.archive`, `scripts.lib.catalog`, and `scripts.lib.product_contract`. Update `SHARED_RELEASE_PATHS` to include `products.toml`, `scripts/release.py`, and relevant `scripts/lib/*.py` files so working-tree checks fail closed on shared release logic.

- [ ] **Step 4: Split archive-manifest logic from its CLI**

Move constants, `CaptureError`, Git helpers, `canonical_bytes`, source/hit classification, `build_manifest`, `verify_manifest`, and `source_problems` to `scripts/lib/archive_manifest.py`. The top-level script retains parser construction, `_run_capture`, `_run_verify`, output formatting, and `main()`, importing reusable functions from the library.

- [ ] **Step 5: Update tests to import only library modules for reusable behavior**

CLI subprocess tests continue to execute the top-level scripts. Unit tests import functions from `scripts.lib.*`. Update the catalog importer source assertion to require `from scripts.lib.archive import`.

- [ ] **Step 6: Run release/catalog/archive tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release tests.repository.test_release_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_catalog_contract tests.repository.test_catalog_release -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_archive_manifest -v
```

Expected: all exit 0; immutable legacy fixture hashes and catalog member sets remain unchanged.

- [ ] **Step 7: Run catalog verification**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --catalog`

Expected: exit 0.

- [ ] **Step 8: Commit tooling consolidation**

```bash
git add scripts tests/repository
git commit -m "refactor: consolidate reusable repository tooling"
```

### Task 8: Separate current documentation from history and remove redirects

**Files:**
- Create: `docs/README.md`
- Create: `docs/history/README.md`
- Move: `docs/superpowers/specs/` -> `docs/history/specs/`
- Move: `docs/superpowers/plans/` -> `docs/history/plans/`
- Delete: `docs/ko/{getting-started,compatibility,evaluation,privacy-and-rights}.md`
- Delete: `docs/en/{getting-started,compatibility,evaluation,privacy-and-rights}.md`
- Create: `docs/maintainers/repository/products-registry.md`
- Create: `docs/maintainers/repository/release.md`
- Rename: `docs/maintainers/repository/catalog-release.md` -> `docs/maintainers/repository/catalog.md`
- Rename: `docs/maintainers/repository/archive-migration.md` -> `docs/maintainers/repository/migrations.md`
- Modify: `docs/maintainers/README.md`, repository guides, product/user/root READMEs, `scripts/lib/archive_manifest.py`, and relevant tests

**Interfaces:**
- Consumes: the physical structure and registry from Tasks 1–7.
- Produces: three clear reader routes, exactly four bilingual user guides per language, task-oriented maintainer docs, and `docs/history/` as the only historical-plan/spec location.

- [ ] **Step 1: Add documentation-structure tests**

```python
def test_only_four_user_guides_exist_per_language(self) -> None:
    expected = {"installation.md", "compatibility.md", "safety-and-privacy.md", "verification.md"}
    for language in ("ko", "en"):
        self.assertEqual({p.name for p in (ROOT / "docs/users" / language).glob("*.md")}, expected)
        self.assertFalse((ROOT / "docs" / language).exists())

def test_history_is_visibly_non_authoritative(self) -> None:
    text = (ROOT / "docs/history/README.md").read_text(encoding="utf-8")
    self.assertIn("현재 계약을 정의하지", text)
    self.assertFalse((ROOT / "docs/superpowers").exists())
```

- [ ] **Step 2: Run documentation tests and confirm old-layout failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_repository -v`

Expected: FAIL because `docs/history`, `docs/README.md`, and repository guides are absent and redirect directories remain.

- [ ] **Step 3: Move history and remove redirect-only files**

Use `git mv docs/superpowers/specs docs/history/specs` and `git mv docs/superpowers/plans docs/history/plans`. Delete the eight redirect stubs with `apply_patch`. Do not alter the moved historical documents except links that would otherwise be broken by the move.

After the move, continue tracking this plan at
`docs/history/plans/2026-08-28-repository-architecture.md`; do not recreate the
old `docs/superpowers/` directory.

- [ ] **Step 4: Add reader routing and history status**

`docs/README.md` must route: install/choose -> `docs/users/`; use a product -> the README pairs under `skills/korean-writing-editor/`, `skills/image-workbench/`, and `skills/graspic/`; maintain/change/release -> `docs/maintainers/`; inspect past decisions -> `docs/history/`. `docs/history/README.md` must say in Korean and English that files are point-in-time records, may contain old names/paths, and do not define the current contract.

- [ ] **Step 5: Rewrite the maintainer index and repository guides**

The index links these tasks: change product behavior, add host support, register a product, verify, release, inspect the immutable catalog, perform migration/archive work, and inspect history. `products-registry.md` documents every schema field and the registry validation command. `release.md` documents standalone check/build/verify-download without current version literals. `catalog.md` explicitly says registry products do not automatically enter v2.0.0. `migrations.md` preserves archive-manifest procedures.

- [ ] **Step 6: Update archive history classification**

In `scripts/lib/archive_manifest.py`, classify `docs/history/` and `docs/operations/` as `skill-history-document`; remove the `docs/superpowers/` active prefix. Update the fixture path and expected classification in `test_archive_manifest.py`.

- [ ] **Step 7: Update all active links and terminology**

Use `rg -n 'docs/superpowers|docs/(ko|en)/|catalog contains these three|스킬 카탈로그' --glob '!docs/history/**' .`. Update active files so “current standalone products” means all registered products and “catalog” means only `catalog/`. General docs must not copy product version literals.

- [ ] **Step 8: Run docs, archive, and catalog contracts**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_repository tests.repository.test_archive_manifest -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --catalog
```

Expected: all exit 0 and no broken active Markdown links.

- [ ] **Step 9: Commit documentation architecture**

```bash
git add docs README.md README.en.md skills scripts/lib/archive_manifest.py tests/repository
git commit -m "docs: separate current guidance from history"
```

### Task 9: Derive documentation facts and links from the registry

**Files:**
- Create: `scripts/lib/documentation.py`
- Modify: `tests/repository/test_public_docs.py`
- Modify: `tests/repository/test_product_registry.py`
- Modify: current root, user, product, and maintainer Markdown files only where tests expose drift

**Interfaces:**
- Consumes: `ProductRegistry` and current Markdown files.
- Produces: `active_markdown_paths(root) -> tuple[Path, ...]`, `markdown_links(path) -> tuple[str, ...]`, `broken_markdown_links(root, paths) -> list[str]`, and registry-driven assertions for product names, install paths, maintainer paths, host claims, and Korean/English parity.

- [ ] **Step 1: Add registry-driven public-doc tests**

```python
def test_root_readmes_cover_registered_products(self) -> None:
    for relative in ("README.md", "README.en.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for product in self.registry.products:
            self.assertIn(product.name, text, relative)
            self.assertIn(product.skill_path.as_posix(), text, relative)

def test_product_readmes_match_registry_hosts(self) -> None:
    for product in self.registry.products:
        for filename in ("README.md", "README.en.md"):
            text = (ROOT / product.skill_path / filename).read_text(encoding="utf-8")
            for host in product.supported_hosts:
                self.assertIn(host, text.lower(), f"{product.name}/{filename}")

def test_all_active_markdown_links_resolve(self) -> None:
    self.assertEqual(broken_markdown_links(ROOT, active_markdown_paths(ROOT)), [])
```

- [ ] **Step 2: Run tests and confirm hard-coded fact drift or missing helper failures**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs -v`

Expected: FAIL because current tests use hard-coded product title/path tuples and `scripts.lib.documentation` is absent.

- [ ] **Step 3: Implement Markdown link helpers**

Support relative Markdown links, URL fragments, angle-bracket paths, and query/fragment stripping. Ignore `http:`, `https:`, `mailto:`, and in-page-only links. Return repository-relative error strings in sorted order. Do not generate prose from TOML.

- [ ] **Step 4: Replace hard-coded product inventories in tests**

Load `products.toml` in the test setup. Assert information order and paired facts from the registry, while retaining hand-written exact safety statements, installer semantics, catalog boundary, and provider-free evidence assertions. Product display copy remains authored Markdown.

- [ ] **Step 5: Run docs and registry tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_public_docs tests.repository.test_product_registry -v`

Expected: PASS.

- [ ] **Step 6: Commit documentation contracts**

```bash
git add scripts/lib/documentation.py tests/repository/test_public_docs.py tests/repository/test_product_registry.py README.md README.en.md docs skills
git commit -m "test: validate documentation against product registry"
```

### Task 10: Prove the foundation is independently green

**Files:**
- Modify only files implicated by a failing acceptance command.
- Do not modify `catalog/catalog.lock.json`, catalog legacy fixture bytes, product versions, or product identities.

**Interfaces:**
- Consumes: every interface and structure created in Tasks 1–9.
- Produces: a clean provider-free baseline that the dependent How It Works plan can start from.

- [ ] **Step 1: Scan for forbidden old architecture paths outside history**

Run:

```bash
rg -n 'tests/contract|tests/(graspic|image-workbench|korean-writing-editor)|docs/maintainers/(graspic|image-workbench|korean-writing-editor)|docs/superpowers|docs/(ko|en)/' --glob '!docs/history/**' .
```

Expected: no matches. Any match is corrected in its owning active file before continuing.

- [ ] **Step 2: Validate registry coverage and repository contracts**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Expected: both exit 0.

- [ ] **Step 3: Run every product selector**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill korean-writing-editor
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill graspic
```

Expected: all exit 0.

- [ ] **Step 4: Run catalog and both profiles**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --catalog
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: all exit 0; no model/provider command runs.

- [ ] **Step 5: Check immutable catalog inputs and legacy fixture bytes**

Run: `git diff --exit-code HEAD^ -- catalog/catalog.lock.json tests/repository/fixtures/legacy-bundle-v2.0.0`

Expected: exit 0 for the final foundation commit. Also run
`git diff --raw --find-renames origin/main...HEAD -- tests/repository/fixtures/legacy-bundle-v2.0.0`
and require only 100%-similarity rename records for the legacy fixture files.

- [ ] **Step 6: Inspect repository state and whitespace**

Run:

```bash
git status --short --branch
git diff --check
git log --oneline --decorate -12
```

Expected: only planned committed changes, no generated archives, no provider responses, no credentials, and no whitespace errors.

- [ ] **Step 7: Commit any acceptance-only corrections**

If Steps 1–6 required tracked corrections, commit exactly those files:

```bash
git add products.toml scripts tests docs README.md README.en.md CONTRIBUTING.md .github
git commit -m "fix: close repository architecture acceptance gaps"
```

If no correction was required, do not create an empty commit.

---

## Completion Gate

This plan is complete only when the current-name repository is fully green, `products.toml` is the sole current product index, all product/test/maintainer directories are mirrored, history is non-authoritative, the catalog remains byte-stable, and no `how-it-works` behavior or local-link migration has started. Then execute `docs/history/plans/2026-08-28-how-it-works.md`.

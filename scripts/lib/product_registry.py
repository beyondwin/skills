from __future__ import annotations

import collections.abc
import dataclasses
import pathlib
import re
import tomllib


KNOWN_HOSTS = frozenset({"codex", "claude-code", "grok", "cursor"})
PRODUCT_KEYS = frozenset({
    "name", "display_name", "skill_path", "test_path", "maintainer_docs",
    "supported_hosts", "owned_paths", "verify_stages",
})
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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
    def names(self) -> tuple[str, ...]:
        return tuple(product.name for product in self.products)

    def require(self, name: str) -> Product:
        for product in self.products:
            if product.name == name:
                return product
        raise KeyError(name)


def normalize_repo_path(value: str | pathlib.PurePath) -> str:
    normalized = str(value).replace("\\", "/").lstrip("./")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized


def load_registry(path: pathlib.Path) -> ProductRegistry:
    try:
        data = tomllib.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"invalid products.toml: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("products.toml must be a table")
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    raw_products = data.get("products")
    if not isinstance(raw_products, list):
        raise ValueError("products must be an array of tables")
    products = tuple(
        _load_product(index, item) for index, item in enumerate(raw_products)
    )
    _reject_duplicates((product.name for product in products), "duplicate product name")
    _reject_duplicates(
        (product.skill_path.as_posix() for product in products),
        "duplicate skill_path",
    )
    _reject_duplicates(
        (product.test_path.as_posix() for product in products),
        "duplicate test_path",
    )
    _reject_duplicates(
        (product.maintainer_docs.as_posix() for product in products),
        "duplicate maintainer_docs",
    )
    _reject_duplicates(
        (
            owned.as_posix()
            for product in products
            for owned in product.owned_paths
        ),
        "duplicate owned path",
    )
    return ProductRegistry(schema_version=1, products=products)


def validate_registry(
    root: pathlib.Path,
    registry: ProductRegistry,
    registered_stages: collections.abc.Collection[str],
) -> list[str]:
    errors: list[str] = []
    root = pathlib.Path(root)
    for product in registry.products:
        for stage in product.verify_stages:
            if stage not in registered_stages:
                errors.append(f"unknown verification stage: {stage}")
        skill_root = root / product.skill_path
        test_root = root / product.test_path
        docs_root = root / product.maintainer_docs
        if not skill_root.is_dir():
            errors.append(f"missing skill directory: {product.skill_path.as_posix()}")
        if not test_root.is_dir():
            errors.append(f"missing test directory: {product.test_path.as_posix()}")
        if not docs_root.is_dir():
            errors.append(
                f"missing maintainer-docs directory: {product.maintainer_docs.as_posix()}"
            )
        if skill_root.name != product.name:
            errors.append(
                f"product {product.name}: skill directory {skill_root.name} "
                "does not match name"
            )
        if skill_root.is_dir():
            errors.extend(_identity_errors(skill_root, product))
    registered = set(registry.names)
    errors.extend(
        _unregistered_children(
            root / "skills",
            "unregistered skill directory: skills",
            registered,
        )
    )
    errors.extend(
        _unregistered_children(
            root / "tests" / "products",
            "unregistered test directory: tests/products",
            registered,
        )
    )
    errors.extend(
        _unregistered_children(
            root / "docs" / "maintainers" / "products",
            "unregistered maintainer-docs directory: docs/maintainers/products",
            registered,
        )
    )
    return errors


def _unregistered_children(
    path: pathlib.Path,
    prefix: str,
    registered: set[str],
) -> list[str]:
    if not path.is_dir():
        return []
    extra = sorted(
        child.name
        for child in path.iterdir()
        if child.is_dir() and child.name not in registered
    )
    return [f"{prefix}/{name}" for name in extra]


def _load_product(index: int, item: object) -> Product:
    if not isinstance(item, dict):
        raise ValueError(f"products[{index}] must be a table")
    label = _product_label(item, index)
    extra = sorted(set(item) - PRODUCT_KEYS)
    if extra:
        raise ValueError(f"product {label}: extra field {extra[0]}")
    missing = sorted(PRODUCT_KEYS - set(item))
    if missing:
        raise ValueError(f"product {label}: missing field {missing[0]}")
    name = _string(label, "name", item["name"])
    if NAME_RE.fullmatch(name) is None:
        raise ValueError(f"product {name}: invalid name")
    display_name = _string(label, "display_name", item["display_name"])
    supported_hosts = _string_list(name, "supported_hosts", item["supported_hosts"])
    unknown_hosts = [host for host in supported_hosts if host not in KNOWN_HOSTS]
    if unknown_hosts:
        raise ValueError(f"product {name}: unknown host {unknown_hosts[0]}")
    verify_stages = _string_list(name, "verify_stages", item["verify_stages"])
    skill_path = _repo_path(name, "skill_path", item["skill_path"], directory=False)
    test_path = _repo_path(name, "test_path", item["test_path"], directory=False)
    maintainer_docs = _repo_path(
        name, "maintainer_docs", item["maintainer_docs"], directory=False
    )
    owned_raw = item["owned_paths"]
    if not isinstance(owned_raw, list):
        raise ValueError(f"product {name}: owned_paths must be a list of strings")
    owned_paths: list[pathlib.PurePosixPath] = []
    seen_owned: set[str] = set()
    for owned in owned_raw:
        parsed = _repo_path(name, "owned_paths", owned, directory=True)
        posix = parsed.as_posix()
        if posix in seen_owned:
            raise ValueError(f"duplicate owned path: {posix}")
        seen_owned.add(posix)
        owned_paths.append(parsed)
    return Product(
        name=name,
        display_name=display_name,
        skill_path=skill_path,
        test_path=test_path,
        maintainer_docs=maintainer_docs,
        supported_hosts=supported_hosts,
        owned_paths=tuple(owned_paths),
        verify_stages=verify_stages,
    )


def _product_label(item: dict[str, object], index: int) -> str:
    name = item.get("name")
    if isinstance(name, str) and name:
        return name
    return f"products[{index}]"


def _string(label: str, field: str, value: object) -> str:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"product {label}: {field} must be a string")
    return value


def _string_list(label: str, field: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"product {label}: {field} must be a list of strings")
    return tuple(value)


def _repo_path(
    label: str,
    field: str,
    value: object,
    *,
    directory: bool,
) -> pathlib.PurePosixPath:
    text = _string(label, field, value)
    if _is_absolute(text):
        raise ValueError(f"product {label}: {field} path must be repository-relative")
    posix = text.replace("\\", "/")
    if ".." in posix.split("/"):
        raise ValueError(f"product {label}: {field} path must be repository-relative")
    if directory != posix.endswith("/"):
        raise ValueError(f"product {label}: {field} must be a trailing directory")
    normalized = normalize_repo_path(text).rstrip("/")
    if not normalized:
        raise ValueError(f"product {label}: {field} path must be repository-relative")
    return pathlib.PurePosixPath(normalized)


def _is_absolute(value: str) -> bool:
    posix = value.replace("\\", "/")
    if posix.startswith("/") or posix.startswith("~"):
        return True
    return pathlib.PureWindowsPath(value).is_absolute()


def _reject_duplicates(values: collections.abc.Iterable[str], message: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"{message}: {value}")
        seen.add(value)


def _identity_errors(skill_root: pathlib.Path, product: Product) -> list[str]:
    errors: list[str] = []
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"product {product.name}: missing SKILL.md")
    else:
        frontmatter_name = _skill_frontmatter_name(skill_md)
        if frontmatter_name != product.name:
            errors.append(
                f"product {product.name}: SKILL.md name {frontmatter_name!r} "
                "does not match registry"
            )
    release_path = skill_root / "release.toml"
    if not release_path.is_file():
        errors.append(f"product {product.name}: missing release.toml")
        return errors
    try:
        data = tomllib.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        errors.append(f"product {product.name}: invalid release.toml: {exc}")
        return errors
    release_name = data.get("name") if isinstance(data, dict) else None
    if release_name != product.name:
        errors.append(
            f"product {product.name}: release.toml name {release_name!r} "
            "does not match registry"
        )
    return errors


def _skill_frontmatter_name(path: pathlib.Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    closing = text.find("\n---", 3)
    if closing < 0:
        return None
    for line in text[3:closing].splitlines():
        stripped = line.strip()
        if stripped.startswith("name:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
    return None

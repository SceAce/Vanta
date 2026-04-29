from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_check_dep_docs_module() -> object:
    root = Path(__file__).resolve().parents[3]
    script = root / "scripts" / "lint" / "check_dep_docs.py"
    spec = importlib.util.spec_from_file_location("check_dep_docs", script)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_deps_normalizes_workspace_dependency_keys(tmp_path: Path) -> None:
    module = _load_check_dep_docs_module()
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(
        "\n".join(
            [
                "[dependencies]",
                "serde.workspace = true",
                "serde_json.workspace = true",
                'time = { workspace = true }',
            ]
        ),
        encoding="utf-8",
    )

    deps = module._parse_deps(cargo_toml)  # type: ignore[attr-defined]

    assert deps == {"serde", "serde_json", "time"}

# Rust Coding Style

## Formatter

- **rustfmt** with workspace `rustfmt.toml` -- 100-character line width, 2024 edition.
- Run: `cargo fmt --all` (auto-fix) / `cargo fmt --all --check` (CI gate).

## Safety

- `unsafe` code is **forbidden** everywhere (`unsafe_code = "forbid"` in workspace lints).
- No exceptions. If you think you need unsafe, redesign the API.

## Error Handling

- **Library crates** (`crates/`): use `thiserror` for typed errors. Every public error enum gets `#[derive(Debug, thiserror::Error)]`.
- **Application crate** (`apps/`): use `anyhow` for ad-hoc errors and context chaining.
- **Never** use `.unwrap()`, `.expect()`, `panic!()`, `todo!()`, `unimplemented!()`, or `dbg!()` in production code. These are **denied by clippy** at the workspace level.
- Tests may use `.unwrap()` freely inside `#[cfg(test)]` blocks.

## Documentation

- Every public item (`pub fn`, `pub struct`, `pub enum`, `pub trait`, `pub type`, `pub const`) requires a `///` doc comment.
- Every crate root (`lib.rs`) requires a `//!` module-level doc comment explaining the crate's purpose.
- Enforced by T-002 lint (`scripts/lint/taste_t002_rustdoc.py`).

## Naming

- **Types**: `UpperCamelCase`
- **Functions/methods**: `snake_case`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Modules**: `snake_case`, flat files preferred (`src/proxy.rs` over `src/proxy/mod.rs`) unless the module has children.

## Marker Comments

- `TODO`, `FIXME`, `HACK`, `STUB`, `XXX` are **forbidden** in production code (`crates/`, `apps/`).
- Track work in GitHub issues instead.
- Permitted only inside `#[cfg(test)]` blocks.
- Enforced by T-003 lint (`scripts/lint/taste_t003_no_marker_comments.py`).

## Function Size

- Non-test functions must be **60 lines or fewer**.
- Extract helpers to reduce size.
- Enforced by T-007 lint (`scripts/lint/taste_t007_fn_size.py`).

## Clippy

Workspace-level denials:

```toml
[workspace.lints.clippy]
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
todo = "deny"
unimplemented = "deny"
dbg_macro = "deny"
```

## Dependencies

- All shared dependencies live in `[workspace.dependencies]` in the root `Cargo.toml`.
- Per-crate `Cargo.toml` files reference workspace deps with `dep.workspace = true`.
- No per-crate version overrides unless absolutely necessary.

## Async

- Runtime: **tokio** (full features).
- `async fn` in traits is fine (Rust 2024 edition).
- Use `spawn_blocking` for CPU-bound work that would block the event loop.

## Tests

- Unit tests go in `#[cfg(test)] mod tests { ... }` at the bottom of each source file.
- Integration tests go in `tests/` directories.
- All test functions should use `-> anyhow::Result<()>` with `?` for assertions where practical.
- Use `assert!(result.is_err())` instead of `#[should_panic]`.

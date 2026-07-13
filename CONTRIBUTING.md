# Contributing

Thanks for your interest. This file documents how the project is
maintained and what to expect.

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).
Given a version `MAJOR.MINOR.PATCH`:

- **MAJOR** bumps when the public API changes in a way that breaks
  existing callers: function removed, signature changed in an
  incompatible way, exception type changed, return shape changed,
  default behavior reversed.
- **MINOR** bumps when functionality is added in a backwards-compatible
  way: new function, new optional parameter, new optional dependency.
- **PATCH** bumps for backwards-compatible fixes only: bug fixes,
  internal refactors, packaging fixes, dependency-pin bumps that
  don't change observable behavior.

### What counts as a breaking change

Counts as breaking (MAJOR bump):

- Removing or renaming a public function / class / attribute.
- Changing a function's positional argument order or making an
  optional argument required.
- Changing the return type, shape, or semantics of a public function.
- Changing the exception class raised for a known error path (e.g.
  going from `ValueError` to `RuntimeError`).
- Removing a public submodule.
- Tightening the supported Python version range.

Does not count as breaking (MINOR / PATCH):

- Adding a new optional argument with a backwards-compatible default.
- Adding a new function or submodule.
- Tightening dependency pins to a newer minor version (assuming the
  new dep is still compatible).
- Loosening dependency pins.
- Internal refactors that preserve observable behavior.
- Type-annotation precision improvements.
- Docstring and README changes.

### Anything underscore-prefixed is private

Names starting with `_` are not part of the public API and may change
between any two releases without a major bump. Don't rely on them in
external code.

## Coding style

Every Python file in this suite follows the same shape (mandate 2026-06-29):

1. **Numpy-style docstring on every function and class.** Sections in order:
   short summary, optional extended summary, `Parameters`, `Returns` /
   `Yields`, `Raises`, `Examples`, `Notes`. Sphinx-friendly underlines
   (`----`).
2. **Module-level header docstring on every `.py` file.** Numpy style, with
   a `Module summary` paragraph, a `Usage example` section, and an
   `Author` section pointing at
   [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui).
3. **Full type annotations.** Parameters, returns, class attributes,
   module-level constants. `from __future__ import annotations` to keep
   forward refs cheap. Prefer `TypedDict` for structured returns
   (already a pattern across the suite).
4. **Generous comments.** Explain the *why* and any non-obvious *how*.
   Comments above blocks, not redundant inline. Cite the trade-off when
   picking an algorithm or backend.
5. **No bare `print(...)` in `.py` code.** Use `os_helper`'s logging
   surface — `osh.info(...)` / `osh.warning(...)` / `osh.error(...)` /
   `osh.debug(...)` — so verbosity is controlled centrally via
   `osh.verbosity(level)`. **Docs (README, LISEZMOI, EXAMPLES.md, docstring
   examples) keep `print(...)`** — tutorial code reads naturally that way.
6. **`print(...)` in docs is followed by a `#`-comment showing expected
   output.** Doctest / REPL style — either trailing inline
   (`print(x)  # 42`) or on the next line (`# 42`).
7. **EXAMPLES.md** at the repo root, linked from README + LISEZMOI. Self-
   contained, runnable cookbook of the helper'''s main use cases.
8. **`*_config.json.example`** for any helper that loads credentials via
   `os_helper.get_config`. Real `*config.json` files are `.gitignore`d;
   the `.example` is committed.
9. **Wherever `brew install <pkg>` appears in the docs**, the line is
   accompanied by `(install `brew` thanks to [brew.sh](https://brew.sh/))`
   when not already obvious from context.

## Releases

Releases live in [`CHANGELOG.md`](CHANGELOG.md) following the
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Each
release is tagged `vX.Y.Z` in git and published as a GitHub release.

Cross-helper dependency pins (e.g. `os-helper @ git+...@v1.3.0`) are
exact-pinned to a specific tag for now. Once helpers are on PyPI we
will move to version ranges.

## CI

GitHub Actions runs `pytest` on Python 3.10 / 3.11 / 3.12 / 3.13
(Linux) plus a non-blocking `ruff` lint job. Integration tests are
gated by `pytestmark = pytest.mark.integration` and skipped by
default (`addopts = -m 'not integration'`).

## Running tests locally

```bash
pip install -e ".[dev]"
pytest -v                 # unit only
pytest -v -m integration  # integration only
pytest -v -m ""           # everything
```

## Authorship

Sole author: [Warith HARCHAOUI](https://linkedin.com/in/warith-harchaoui).
External contributions are welcome — please open an issue or PR.

Special thanks to [Mohamed Chelali](https://mchelali.github.io) and
[Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug) for fruitful
discussions throughout the suite's evolution.

## License

[BSD-3-Clause](LICENSE) — same as scikit-learn / numpy / scipy.

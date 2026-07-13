# Some Coding Standards

A practical coding standard for Python projects that should be readable, maintainable, testable, and easy for downstream users to adopt.

The goal: every project should read like a **teaching artefact**, not a private side project. Examples, docstrings, types, tests, and clear documentation are part of the public contract with users and contributors.

---

## 0. Scope: all functions, all languages, no exceptions

These standards apply to **every function, method, and class**, including:

* Private and internal functions (`def _helper`, `def __internal`)
* Dunder methods (`__init__`, `__repr__`, `__eq__`, ...)
* Nested functions, closures, lambdas promoted to named functions
* Module-private helpers and script-only utilities

There is **no exemption based on naming convention or visibility**. A leading underscore signals *intended audience*, not *lower quality*. Private code must meet the same documentation, typing, commenting, and testing bar as public code.

This scope also applies across **all languages present in the repository**, not only Python. If the project contains JavaScript/TypeScript (`_name`), shell scripts, Rust, Go, C/C++ (`_name`, `name_`), or any other language, the equivalent conventions of that language apply with the same "no private-code exemption" rule:

* Every function gets a doc comment (JSDoc, rustdoc, GoDoc, Doxygen, shell header comment, ...)
* Every function is typed to the extent the language allows
* Every function is covered by tests

Do not silently omit a language, a file, or a function from these rules.

---

## 1. Use Numpy-style docstrings for every function and class

Every function and class — **public or private, including `def _*` and `def __*`** — should include a Numpy-style docstring.

Recommended sections, in order:

* Short summary
* Optional extended summary
* `Parameters`
* `Returns` or `Yields`
* `Raises`
* `Examples`
* `Notes`

Use Sphinx-friendly underlines.

```python
def add(a: int, b: int) -> int:
    """Return the sum of two integers.

    Parameters
    ----------
    a : int
        First operand.
    b : int
        Second operand.

    Returns
    -------
    int
        ``a + b``.

    Examples
    --------
    >>> add(2, 3)
    5
    """
    return a + b
```

Private helpers follow the same rules:

```python
def _normalize_name(raw: str) -> str:
    """Normalize a raw user-provided name for comparison.

    Parameters
    ----------
    raw : str
        Name as typed by the user, possibly with stray whitespace
        or inconsistent casing.

    Returns
    -------
    str
        Lower-cased, stripped name suitable for dictionary keys.

    Examples
    --------
    >>> _normalize_name("  Alice ")
    'alice'
    """
    return raw.strip().lower()
```

For private functions, the `Examples` section may be shortened when the function is trivial, but the summary, `Parameters`, and `Returns` sections are always required.

---

## 2. Add a module-level docstring to every `.py` file

Every Python file should start with a module-level docstring. This includes private modules (`_internal.py`, `_utils.py`) — no exceptions.

It should explain what the module does, why it exists, what it consumes, and what it produces.

Suggested structure:

```python
"""
Short one-line description.

Module summary
--------------
Longer paragraph explaining what this module does, why it exists,
what it consumes, and what it produces.

Usage example
-------------
>>> from mypkg import my_function
>>> my_function(42)
42

Author
------
Project maintainer or organization name.
"""
```

For public templates, use neutral attribution such as:

```text
Author
------
Project maintainers.
```

---

## 3. Use full typing

Type-annotate **every** function signature — public, private (`_*`), name-mangled (`__*`), and dunder methods — including parameters and return values.

Also type-annotate class attributes (including private attributes like `_cache`) and module-level constants where reasonable.

Prefer:

```python
from __future__ import annotations
```

Use `TypedDict`, `dataclasses`, `Protocol`, or `pydantic` models when returning or passing structured data.

Example:

```python
from __future__ import annotations

from typing import TypedDict


class UserRecord(TypedDict):
    """Represent a normalized user record."""

    id: int
    name: str
    is_active: bool
```

Private example — same rigor:

```python
def _load_cache(path: Path) -> dict[str, UserRecord]:
    """Load the on-disk user cache."""
    ...
```

---

## 4. Comment generously — everywhere, in every function

Comment **a lot**. Good old comments are a first-class deliverable of this standard, not decoration. Code without comments is considered incomplete, exactly like code without tests.

This rule applies **everywhere, with no exceptions**:

* Public functions and private functions (`_*`, `__*`)
* Dunder methods, nested functions, one-liners with non-obvious intent
* Scripts, tests, CI files, configuration, shell scripts
* Every language in the repository (`#`, `//`, `/* */`, `<!-- -->`, `--`, `;` — use whatever the language provides)

Practical expectations:

* Every **logical block** of code (a loop, a branch, a transformation step, a tricky expression) gets a comment above it explaining what it does and **why**.
* A reader should be able to follow the flow of any function by reading **only the comments**, top to bottom, like a narrated story.
* When in doubt, add the comment. Over-commenting is a much cheaper problem than under-commenting.
* Prefer block comments above the code rather than cramped inline comments — but short inline comments are fine for clarifying a single value or condition.

Recommended ratio:

* **Target ≈ 1 comment line for every 3–4 lines of code** (≈25–30 % density), measured per file, **docstrings excluded**. Docstrings are excluded so the ratio measures actual in-code narration, not API documentation — a file can be fully docstringed and still have zero comments inside its function bodies, which is exactly what this ratio is designed to catch.
* **Higher density is never a defect.** There is no upper limit: going well above the target because the code genuinely needs the narration is encouraged, not tolerated.
* **Floor: never below 1 comment line per 6 lines of code** (≈15 %) in any source file. A file under the floor is treated like a file with missing tests: fix it before merging.
* Trivial glue files (short `__init__.py`, re-export modules) may fall below the floor, but they still need their module docstring.

Measuring the ratio is easy and can be wired into CI:

```bash
# cloc reports code vs comment lines per language and per file.
cloc --by-file src/
```

The ratio is a guardrail, not a game: padding files with parrot comments to
hit the number defeats the purpose and should be rejected in review.

Good comments explain:

* Why a library was chosen
* Why an algorithm or trade-off was selected
* Why an edge case matters
* Why a constraint exists
* What a non-obvious block is about to do, before it does it

The only bad comment is one that merely parrots trivial code (`i += 1  # increment i`). Everything else is welcome.

```python
def _merge_records(base: dict[str, int], patch: dict[str, int]) -> dict[str, int]:
    """Merge ``patch`` into ``base`` without mutating either input."""
    # Work on a copy: callers rely on `base` staying untouched,
    # and silent mutation bugs here are painful to track down.
    merged = dict(base)

    # Apply the patch entries one by one. We iterate explicitly
    # (rather than merged.update(patch)) because we want to skip
    # sentinel values below.
    for key, value in patch.items():
        # A value of -1 is our "delete this key" sentinel, coming
        # from the legacy import format. Remove instead of storing it.
        if value == -1:
            merged.pop(key, None)
            continue

        # Normal case: patch wins over base on conflicts.
        merged[key] = value

    return merged
```

```python
# We normalize paths before comparison because Windows paths are
# case-insensitive while POSIX paths are not.
normalized_path = path.resolve()
```

---

## 5. Include an `EXAMPLES.md` file at the repository root

Every project should include a self-contained, runnable cookbook of its main use cases.

`EXAMPLES.md` should:

* Be written in English
* Contain practical examples users can copy and run
* Cover the most common workflows
* Be linked from `README.md`
* Be linked from localized documentation when relevant

Example README mention:

```markdown
See [`EXAMPLES.md`](EXAMPLES.md) for more recipes.
```

---

## 6. Avoid bare `print(...)` in library and script code

Do not use bare `print(...)` in actual `.py` source files. This includes private modules and private functions — a `print` hidden inside `_debug_helper` is still a `print`.

Use a proper logging surface instead:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing started")
```

This keeps verbosity controlled from one place rather than scattered across the codebase.

Exception: documentation snippets may use `print(...)` because tutorials should remain simple to read.

Allowed places for `print(...)`:

* `README.md`
* `EXAMPLES.md`
* localized docs
* docstring examples
* tutorials

---

## 7. Document expected output after `print(...)` in examples

When documentation examples use `print(...)`, show the expected output with a comment.

```python
result = add(2, 3)
print(result)  # 5
```

Or:

```python
print(add(2, 3))
# 5
```

This helps readers understand the example without running it.

---

## 8. Provide example config files when credentials are needed

Any project that loads credentials should include a committed example config file.

Examples:

```text
app_config.json.example
database_config.json.example
secrets.yaml.example
```

The example file should include:

* Required keys
* Optional keys
* Dummy values
* **Profuse comments** whenever the format allows them

Comment-friendly formats (YAML, TOML, JSONC, INI, `.env`) should be **heavily commented** — this is rule 4 applied to configuration. In particular, every dummy value must be accompanied by a comment explaining:

* **What** the value is and what it is used for
* **How to obtain the real value** (which dashboard, which page, which command)
* **What a valid value looks like** (format, length, prefix)
* Whether the key is **required or optional**, and its default

Prefer YAML over plain JSON for new config files precisely because YAML supports comments. If you must use JSON, consider `.jsonc` or move the explanations into `README.md`.

Fully-commented YAML example:

```yaml
# secrets.yaml.example
# --------------------
# Copy this file to `secrets.yaml` and replace every dummy value.
#   cp secrets.yaml.example secrets.yaml
# `secrets.yaml` is gitignored (see rule 9) — never commit real values.

# REQUIRED — API key for the Example.com service.
# How to get it: log in at https://dashboard.example.com,
# then Settings > API Keys > "Create key".
# Real keys look like: `exk_live_` followed by 32 hex characters.
api_key: "replace-with-your-api-key"   # e.g. exk_live_0123abcd...

# REQUIRED — Base URL of the API.
# Keep the default unless you are on a self-hosted instance.
base_url: "https://api.example.com"

# OPTIONAL — Request timeout in seconds (default: 30).
# Raise this if you process large uploads on a slow connection.
timeout_seconds: 30

# OPTIONAL — SMTP password for outgoing notification emails.
# How to get it: ask your mail provider for an "app password";
# do NOT reuse your personal account password here.
# Leave empty to disable email notifications entirely.
smtp_password: ""
```

JSON fallback (no comments possible — keep values self-describing and
document each key in `README.md` instead):

```jsonc
{
  "api_key": "replace-with-your-api-key",
  "base_url": "https://api.example.com",
  "timeout_seconds": 30
}
```

Reference the example file from:

* `README.md`
* `EXAMPLES.md`
* localized documentation, if any

---

## 9. Gitignore real config files, but keep examples tracked

If a project ships a config example, real config files should be ignored.

Example `.gitignore`:

```gitignore
*config.json
!*config.json.example
```

This prevents accidental secret commits when users copy:

```text
app_config.json.example -> app_config.json
```

---

## 10. Add a Homebrew hint after every `brew install` mention

Whenever documentation includes:

```markdown
brew install <package>
```

The next visible block should mention Homebrew installation:

```markdown
- macOS 🍎 : `brew install ffmpeg`
  (install `brew` thanks to [brew.sh](https://brew.sh/))
```

This helps first-time macOS users find the required package manager.

---

## 11. Keep acknowledgements optional and project-specific

Acknowledgements should be neutral and easy to adapt.

Suggested English form:

```markdown
Special thanks to the contributors, reviewers, and users who helped improve this project.
```

Suggested French form:

```markdown
Remerciements chaleureux aux contributrices, contributeurs, relectrices, relecteurs et utilisateurs qui ont aidé à améliorer ce projet.
```

For public templates, avoid hard-coding personal names unless the project explicitly requires them.

---

## 12. Provide cross-platform install instructions

Every OS-level dependency should include installation instructions for the three canonical desktop platforms:

* macOS 🍎
* Ubuntu 🐧
* Windows 🪟

Canonical block:

```markdown
- macOS 🍎 : `brew install ffmpeg`
  (install `brew` thanks to [brew.sh](https://brew.sh/))
- Ubuntu 🐧 : `sudo apt install ffmpeg`
- Windows 🪟 : `winget install ffmpeg`
```

If a package is genuinely unavailable on a platform, say so explicitly.

Example:

```markdown
- Windows 🪟 : no first-party Windows package — build from source or use WSL2.
```

Do not silently omit a platform.

---

## 13. Keep AI-assistant attribution policy explicit

For projects using AI assistance, decide whether AI tools should appear in public attribution.

Recommended default for most repositories:

* Do not list AI assistants as authors, contributors, or co-authors.
* Do not add AI-generated `Co-Authored-By` trailers to commits.
* Attribute human maintainers and contributors only.
* Mention AI tooling only when the project policy explicitly allows it.

Example policy:

```markdown
AI tools may be used during development, but authorship and responsibility remain with the human maintainers. Commit authorship, release notes, and contributor lists should name only human contributors unless the project governance explicitly states otherwise.
```

If past public history contains unwanted AI attribution, do not rewrite shared history casually. Rewriting public Git history is destructive and should be scoped, discussed, and approved first.

---

## 14. Use `pytest` and require CI to pass

Every Python project should ship:

* A `tests/` directory
* `pytest`-based tests
* A CI workflow that runs on every push and pull request

Recommended requirements:

* Use plain `pytest` functions and fixtures where possible.
* Put shared fixtures in `tests/conftest.py`.
* Mirror the source tree as the project grows.
* Ensure **every function and class is covered at least once, including private ones** (`_helper`, `__internal`) — coverage may come from functional/scenario tests that exercise many functions at once; a dedicated test per function is not required (see the 100-test rule below).
* Prefer meaningful coverage over chasing 100% coverage.
* Track coverage with `pytest-cov` when useful.
* Keep tests deterministic.
* Seed randomness.
* Mock network, disk, and clock boundaries.
* Mark slow integration tests with `@pytest.mark.slow`.
* Keep the fast test suite runnable in seconds.

Example local command:

```bash
pytest -q
```

With coverage:

```bash
pytest --cov=mypkg tests/
```

Document the exact CI command in:

* `README.md`
* `EXAMPLES.md`
* localized documentation, if any

A failing test should block merging to the main branch.

### Rationalize the suite at the 100-test mark

Test count is not a quality metric. When a project's suite reaches **~100 tests**, stop and rationalize before adding more:

* **Prefer quality over quantity.** A smaller suite of meaningful, well-named, well-commented tests beats a sprawling suite of mechanical ones.
* **Move away from the "one test / one function" schema.** Early on, one unit test per function is a fine bootstrap. At scale it produces brittle, redundant tests that mirror the implementation and break on every refactor.
* **Prefer functional tests that cover several use cases end-to-end.** One scenario test that walks a realistic workflow (load config → ingest data → transform → export) exercises many functions at once, catches integration bugs unit tests miss, and documents how the project is actually used.
* **Merge and prune.** Fold overlapping micro-tests into parameterized tests (`@pytest.mark.parametrize`) or scenario tests; delete tests that only re-verify what another test already proves.
* **Keep targeted unit tests where they earn their place**: tricky algorithms, edge cases, regression tests pinned to a past bug (with a comment referencing the issue).

Practical rhythm: at ~100 tests, hold a suite review. Ask of each test: *what failure would this catch that nothing else catches?* If the answer is "none", merge it or delete it. Coverage should stay stable or improve during rationalization — the goal is fewer, stronger tests, not less protection.

---

## 15. Add AI evaluation when the project uses AI

For projects involving AI, regular unit tests are not enough.

This applies to projects using:

* LLM prompts
* RAG
* Agents
* Embeddings
* Generative models
* Classical ML models
* Model inference pipelines

Add an evaluation layer with at least one dedicated framework.

Recommended options:

* [DeepEval](https://github.com/confident-ai/deepeval) for LLM-focused evaluation
* [Giskard](https://github.com/Giskard-AI/giskard) for ML and LLM testing

AI evaluation should include:

* A committed evaluation dataset
* Explicit metrics
* Versioned thresholds
* CI gating
* Model and dataset pinning
* Cost controls such as cached LLM responses
* A human-review path for open-ended generation

Example thresholds:

```text
answer_relevancy > 0.70
hallucination_rate < 0.05
robustness_score > 0.90
```

Do not rely on “vibe checks” as the only validation layer.

---

## How to apply these standards

When editing an existing `.py` file:

1. Bring the touched file closer to compliance.
2. Add missing types and docstrings where practical — including on private `_*` functions.
3. Add comments to every logical block you touch — the edited code should read like a narrated story.
4. Avoid leaving newly edited code half-styled.
5. Add or update tests for changed behavior.

When creating a new `.py` file:

1. Add `from __future__ import annotations`.
2. Add a module-level docstring.
3. Type all functions and classes, private ones included.
4. Add Numpy-style docstrings to all functions and classes, private ones included.
5. Comment every logical block generously, from the very first draft — never "I'll add comments later".
6. Add tests from the start.

When making a documentation-only or style-only release:

1. Use a patch version bump if appropriate.
2. Update `CHANGELOG.md`.
3. Group the change under a `Documentation` or `Maintenance` section.

---

## Core principle

A good repository should be understandable by a new reader, testable by a contributor, reproducible in CI, and usable without private context.

Documentation, examples, typing, tests, and evaluation are not extras. They are part of the software — for every function, in every language, with no private-code exceptions.

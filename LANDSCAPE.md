# Landscape

[🇫🇷 PAYSAGE.md](https://github.com/warith-harchaoui/os-helper/blob/main/PAYSAGE.md) · 🇬🇧 English

Related and competing Python libraries in the "cross-platform OS +
filesystem + config helper" space, benchmarked against `os-helper`.
Ratings are ⭐ (1) to ⭐⭐⭐⭐⭐ (5), scored on `os-helper`'s intended
job: utility glue for AI pipelines (OS detection, path handling,
hashing, config loading, temp scratch, smart downloads, small
subprocess wrappers, colored logging). A library optimised for a very
different job (e.g. full-blown async filesystem, cloud object storage)
is not penalised; the score just reflects fit to *this* niche.

## At a glance

<!-- TABLE:START -->
| OS Management | Cross-OS detection | Path helpers | Hashing | Config loading | Temp scratch | Smart downloads | Multi-surface | Suite cohesion |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **os-helper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| stdlib os | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| click | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ |
| python-dotenv | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| pydantic-settings | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| PyYAML | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| requests | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| psutil | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| sh | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ |
| fsspec | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| smart_open | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ |
| pooch | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| platformdirs | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ |
<!-- TABLE:END -->

## Positioning map

<!-- FIGURE:START -->
2D representation of the table above.

![Positioning map](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/landscape.png)

The map is a 2-D summary of the eight criteria, so read it as a shape, not a scoreboard. `os-helper` is at the top-right corner. The axes read **Horizontal — Adaptable ↔ Resourceful** and **Vertical — Practical ↔ Complete**.
<!-- FIGURE:END -->

## Positioning

`os-helper` deliberately sits at the intersection of **stdlib
completeness** (nothing here is exotic; every primitive maps to
`os` / `pathlib` / `hashlib` / `tempfile` / `dotenv` / `yaml`) and
**AI-pipeline ergonomics** (colored ``info`` / ``warning`` / ``error``
logging, ``verbosity(-2..2)`` shortcuts, ``dict`` returns from
``system()`` / ``get_config()`` / ``get_user_ip()``, ``get_nb_workers``
following the sklearn ``n_jobs`` convention, hash-verified smart
downloads with local caching, remote-staging context manager for
object-storage backends, a one-call hardware snapshot for CPU/RAM/GPU).
It intentionally does **not** try to compete with `pooch` on
scientific-data fetching, `fsspec` on remote filesystems, `psutil` on
deep per-process telemetry (memory maps, CPU affinity, per-process I/O
counters), or `pydantic-settings` on typed configuration.

Where `os-helper` uniquely wins in the family:

1. **Multi-surface exposure**. Every helper is reachable from Python,
   an HTTP API (FastAPI), MCP tools (for agents) and the Tree Radar GUI,
   all sharing the same function signatures, no drift. There is no
   command line: wrapping `path exists` in a shell command restated what
   the shell already said, so both CLIs went in 3.0.0.
2. **Zero heavy runtime deps** for the core (`requests`, `pyyaml`,
   `python-dotenv`, `validators`). Every surface is an optional extra,
   so `pip install os-helper` stays lean for library users.
3. **Foundation of the AI Helpers family**: every other `*-helper`
   package imports from ``os_helper`` for logging, path handling,
   temp scratch, hashing and config. It is the layer everything else
   sits on.

## When to pick what

- **`os-helper`**: everyday scripts and libraries in the AI Helpers
  suite: consistent logging, cross-platform paths, "just give me a
  hash / a temp folder / a `.env` value" ergonomics.
- **stdlib `pathlib`**: when you want zero third-party deps and are
  fine wiring up your own logging / config / hashing.
- **`click` / `typer`**: when the CLI *is* the product. os-helper is not
  one: it ships no command line at all, only the three surface launchers
  (`os-helper-api`, `os-helper-mcp`, `os-helper-gui`), so reach for click
  directly rather than for a wrapper here.
- **`pydantic-settings`**: when configuration is complex, typed, and
  validated against a schema.
- **`fsspec` / `smart_open`**: when you need a uniform filesystem
  abstraction across S3 / GCS / Azure / local disks.
- **`pooch`**: when you need hash-verified downloads of scientific
  data files with a registry, integrity checks, and local caching.
- **`platformdirs`**: when all you need is the canonical cross-OS
  user directories (cache / config / data) and nothing else.
- **`psutil`**: when you need deep per-process system telemetry
  (memory maps, CPU affinity, per-process I/O counters) beyond
  `os-helper`'s one-call CPU/RAM/GPU hardware snapshot.

## Sources and as-of date

**As of 2026-10-27**, comparing `os-helper` 3.1.0 (this repository) against the
libraries named above.

The ⭐ ratings are a reading of each project's **documented scope**, not a
benchmark: nothing here was timed, and no claim is made about anyone's code
quality. Read a cell as "how much of this column does the project set out to
do", and read the project's own documentation before betting on it.

`os-helper`'s own row is measured in this repository rather than asserted: the
public surface exported by `os_helper/__init__.py`, the HTTP routes the API
declares (`/health`, `/os`, `/hardware`, `/hash/string`, `/str/ascii`,
`/misc/format-size`, `/misc/now`, `/misc/url-ok`, `/config`) and the three
console scripts in `pyproject.toml`. "Suite cohesion" is a count, not an
opinion: all sixteen other AI Helpers members import `os_helper` from their
package source.

Every other row comes from that project's own documentation:

| Row | Source |
|---|---|
| stdlib os | [docs.python.org — `os.path`](https://docs.python.org/3/library/os.path.html) |
| click | [click.palletsprojects.com](https://click.palletsprojects.com/) |
| python-dotenv | [saurabh-kumar.com/python-dotenv](https://saurabh-kumar.com/python-dotenv/) |
| pydantic-settings | [docs.pydantic.dev — settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| PyYAML | [pyyaml.org — documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) |
| requests | [requests.readthedocs.io](https://requests.readthedocs.io/en/latest/) |
| psutil | [psutil.readthedocs.io](https://psutil.readthedocs.io/en/latest/) |
| sh | [sh.readthedocs.io](https://sh.readthedocs.io/en/latest/) |
| fsspec | [filesystem-spec.readthedocs.io](https://filesystem-spec.readthedocs.io/en/latest/) |
| smart_open | [github.com/piskvorky/smart_open](https://github.com/piskvorky/smart_open) |
| pooch | [fatiando.org/pooch](https://www.fatiando.org/pooch/latest/) |
| platformdirs | [platformdirs.readthedocs.io](https://platformdirs.readthedocs.io/en/latest/) |

Every link above answered HTTP 200 when checked on 2026-10-27. No version
number of a third-party library is quoted anywhere in this document, on
purpose: a pinned version in a comparison rots into a claim about software
nobody re-read.

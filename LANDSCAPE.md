# Landscape

[🇫🇷 PAYSAGE.md](https://github.com/warith-harchaoui/os-helper/blob/main/PAYSAGE.md) · 🇬🇧 English

Related and competing Python libraries in the "cross-platform OS +
filesystem + config helper" space, benchmarked against `os-helper`.
Ratings are ⭐ (1) to ⭐⭐⭐⭐⭐ (5), scored on `os-helper`'s intended
job — utility glue for AI pipelines (OS detection, path handling,
hashing, config loading, temp scratch, small subprocess wrappers,
colored logging). A library optimised for a very different job (e.g.
full-blown async filesystem, cloud object storage) is not penalised —
the score just reflects fit to *this* niche.

## At a glance

<!-- TABLE:START -->
| OS Management | Cross-OS detection | Path helpers | Hashing | Config loading | Temp scratch | Multi-surface | Suite cohesion |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **os-helper** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| stdlib os | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ |
| click | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ |
| python-dotenv | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| pydantic-settings | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐ |
| PyYAML | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| requests | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| psutil | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| sh | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ |
| fsspec | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| loguru | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| smart_open | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ |
<!-- TABLE:END -->

## Positioning map

<!-- FIGURE:START -->
2D representation of the table above.

![Positioning map](https://raw.githubusercontent.com/warith-harchaoui/os-helper/main/assets/landscape.png)

The map is a 2-D summary of the seven criteria, so read it as a shape, not a scoreboard. `os-helper` is at the top-right corner. The axes read **Horizontal — Efficient ↔ Versatile** and **Vertical — Navigable ↔ Integrated**.
<!-- FIGURE:END -->

## Positioning

`os-helper` deliberately sits at the intersection of **stdlib
completeness** (nothing here is exotic; every primitive maps to
`os` / `pathlib` / `hashlib` / `tempfile` / `dotenv` / `yaml`) and
**AI-pipeline ergonomics** (colored ``info`` / ``warning`` / ``error``
logging, ``verbosity(-2..2)`` shortcuts, ``dict`` returns from
``system()`` / ``get_config()`` / ``get_user_ip()``, ``get_nb_workers``
following the sklearn ``n_jobs`` convention, remote-staging context
manager for object-storage backends). It intentionally does **not**
try to compete with `fsspec` on remote filesystems, `psutil` on
system telemetry, or `pydantic-settings` on typed configuration.

Where `os-helper` uniquely wins in the family:

1. **Multi-surface exposure**. Every helper is reachable from Python,
   from an argparse CLI, and from a click CLI — the same function
   signatures, no drift.
2. **Zero heavy runtime deps** for the core (`requests`, `pyyaml`,
   `python-dotenv`, `validators`). The click CLI is an optional extra
   so `pip install os-helper` stays lean for library users.
3. **Foundation of the AI Helpers family**: every other `*-helper`
   package imports from ``os_helper`` for logging, path handling,
   temp scratch, hashing and config. It is the layer everything else
   sits on.

## When to pick what

- **`os-helper`** — every day scripts and libraries in the AI Helpers
  suite: consistent logging, cross-platform paths, "just give me a
  hash / a temp folder / a `.env` value" ergonomics.
- **stdlib `pathlib`** — when you want zero third-party deps and are
  fine wiring up your own logging / config / hashing.
- **`click` / `typer`** — when the CLI *is* the product and you want
  richer decorators / shell completion out of the box (we ship a click
  twin already, so both worlds are covered).
- **`pydantic-settings`** — when configuration is complex, typed, and
  validated against a schema.
- **`fsspec` / `smart_open`** — when you need a uniform filesystem
  abstraction across S3 / GCS / Azure / local disks.
- **`psutil`** — when you need deep system telemetry (memory maps,
  CPU affinity, per-process I/O counters).
- **`loguru`** — when you want a fully custom, structured logging
  stack (os-helper wraps ``logging`` and stays interoperable).

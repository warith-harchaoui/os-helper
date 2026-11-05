# GUI — OS Helper

> A design plan. os-helper ships no command line: the library and the
> shell already handle "one path at a time, one predicate at a time". A
> GUI must go further, otherwise why build one? This document lays out an ambitious, opinionated
> visual product for the "make a folder legible" workflow.

## North star

> **A live, auditable dashboard for the state of a directory tree:
> one screen that turns "what is on disk" into a decision.**

Filesystem work is inherently exploratory (ls → glob → hash → clean up
→ zip → ship). The library and the shell are fine when you know what you want. The GUI's
job is to show you what you *have* (sizes, dupes, hashes, permissions,
staleness) at a glance, and to let you act on it with keyboard
shortcuts.

## What ships today

Milestone M0 with part of M1, read-only: `pip install "os-helper[gui]"`,
then `os-helper-gui --root <folder>` (flags `--root`, `--host`, `--port`;
default `127.0.0.1:8017`). FastAPI serves the page at `GET /gui` and the
scanned tree as JSON at `GET /api/tree` (`root`, `depth` from 1 to 64,
default 12, `dedupe=1` to hash files and group duplicates). The Tree Radar
colours by age, by hash-dedupe cluster or by type family, and speaks French
and English (`?lang=fr` / `?lang=en`). The page is server-rendered HTML
drawn with D3, loaded from the jsDelivr CDN, not the Svelte stack planned
below. It has no action yet: no trash, no zip, no Dedupe Lens, no Config
Explorer, no hash cache on disk.

## Three surfaces, one product

### 1. Tree Radar *(primary surface)*

- Zoomable **treemap** of a chosen root folder. Each rectangle is a
  file or subfolder; area = size, color = one of:
  - **age** (blue = recent, red = stale)
  - **hash-dedupe status** (grey = unique, gold = duplicate cluster)
  - **type family** (code / data / media / archive / other)
- Hover reveals: absolute path, size (human-readable via
  ``format_size``), last-modified timestamp, RIPEMD-160 hash (or
  BLAKE2b fallback) computed on demand and cached.
- Click a rectangle → drills in. Right-click → contextual actions:
  *copy path*, *reveal in Finder / Nautilus / Explorer*, *hash*,
  *delete (best-effort)*, *zip subtree*.

### 2. Dedupe Lens

Splits the screen into two panes. Left: the current folder as a list.
Right: the group of files that share the *same content hash* as the
selected entry (``hashfile``). Instant answer to "do I have four
copies of this?" without leaving the app. Actions:

- ``⌘/Ctrl+D`` on a duplicate cluster → moves all but the newest to a
  local ``.trash-<timestamp>/`` folder, ready for review.
- Undo pushes them back with metadata preserved (``copyfile``).

### 3. Config Explorer

Drop a ``.env`` / ``config.json`` / ``config.yaml`` into a rectangle.
The app runs ``get_config`` for a caller-supplied set of keys, shows
which source wins (file > .env > environ), and reveals shadowed values
side-by-side. Instant answer to "which key is my app actually reading?".

## Design principles

- **Nothing invisible.** Every operation shows its effect on disk
  (size deltas, hash mismatches, permission changes) in real time.
- **Hashes are cheap after the first pass.** The GUI's own cache lives
  in ``~/.cache/os-helper-gui/`` and is invalidated by mtime + size,
  so re-opening the same tree is instant.
- **Keyboard first.** ``/`` opens a fuzzy filter. ``h`` hashes.
  ``d`` toggles the Dedupe Lens. ``z`` zips the current selection.
- **Files, not blobs.** Every action produces a real on-disk artifact
  and logs the exact Python call that would reproduce it: reproducible
  by construction.
- **Colorblind-safe by construction.** Treemap encodings always ship a
  shape/pattern fallback (see companion ``sprezzature-colors`` audit skill).
- **No telemetry.** The GUI is a thin client on top of the local
  os-helper library; nothing leaves the box.

## What we deliberately don't do

- **No file manager rewrite.** Finder / Nautilus / Explorer exist. The
  GUI does one job: make a folder *legible* fast.
- **No cloud sync.** ``download_file`` remains a library concern;
  the GUI opens what is already on disk.
- **No live shell.** ``system()`` and the shell itself cover that already, and a
  live shell inside a GUI is a rabbit hole with no bottom.

## Stack

- Front end: TypeScript + Svelte 5 + D3 (treemap layout) +
  ``@lucide/svelte`` icons. No React; matches the ``sprezzature-ui``
  companion skill's stack.
- Back end: the ``os_helper`` library already covers
  100 % of the read/compute operations. GUI is a thin client that calls
  into the library only.
- Recipe format: the "what did I just do" panel emits a shell script
  and a JSON transcript, versioned per session.

## Milestones

| Milestone | What ships | Why first |
| --- | --- | --- |
| M0 | Tree Radar with mtime coloring on one chosen root. | Prove the treemap metaphor works on a real 200k-file tree. |
| M1 | Hash on demand + hash cache + "what changed since last open?" overlay. | Makes the Radar useful across sessions. |
| M2 | Dedupe Lens with safe move-to-trash + undo. | Turns audit into action. |
| M3 | Config Explorer for ``.env`` / JSON / YAML. | Makes the config precedence rule visible for the first time. |
| M4 | "Prepare release" flow: pick a subtree, hash, describe, zip, upload, all in one keyboard shortcut chain. | Ties the whole helper together into a shippable artifact. |

## Non-goals (recorded so we do not drift)

- Not a file manager.
- Not a hosted SaaS.
- Not a substitute for scripts in CI (the "what did I just do" panel
  emits shell scripts that CI can replay headless).

## Success metric

> A user who inherits a 500 GB scratch drive with 400k files can
> answer "what's here, what's duplicated, what's safe to zip and
> archive" in one afternoon, in one window, and leaves with a
> committable ``cleanup.sh``.

If we ship that, we win.

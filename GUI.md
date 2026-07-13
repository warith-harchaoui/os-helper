# GUI — OS Helper

> A design plan, not a CLI mirror. The CLI already handles "one path at
> a time, one predicate at a time". A GUI must go further — otherwise
> why build one? This document lays out an ambitious, opinionated
> visual product for the "make a folder legible" workflow.

## North star

> **A live, auditable dashboard for the state of a directory tree —
> one screen that turns "what is on disk" into a decision.**

Filesystem work is inherently exploratory (ls → glob → hash → clean up
→ zip → ship). The CLI is fine when you know what you want. The GUI's
job is to show you what you *have* — sizes, dupes, hashes, permissions,
staleness — at a glance, and to let you act on it with keyboard
shortcuts.

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

- **Nothing invisible.** Every operation shows its effect on disk —
  size deltas, hash mismatches, permission changes — in real time.
- **Hashes are cheap after the first pass.** The GUI's own cache lives
  in ``~/.cache/os-helper-gui/`` and is invalidated by mtime + size,
  so re-opening the same tree is instant.
- **Keyboard first.** ``/`` opens a fuzzy filter. ``h`` hashes.
  ``d`` toggles the Dedupe Lens. ``z`` zips the current selection.
- **Files, not blobs.** Every action produces a real on-disk artifact
  and logs the exact CLI command that would reproduce it — reproducible
  by construction.
- **Colorblind-safe by construction.** Treemap encodings always ship a
  shape/pattern fallback (see companion ``front-colors`` audit skill).
- **No telemetry.** The GUI is a thin client on top of the local
  os-helper library / CLI; nothing leaves the box.

## What we deliberately don't do

- **No file manager rewrite.** Finder / Nautilus / Explorer exist. The
  GUI does one job: make a folder *legible* fast.
- **No cloud sync.** ``download_file`` remains a library / CLI concern;
  the GUI opens what is already on disk.
- **No live shell.** ``os-helper os run`` covers that already, and a
  live shell inside a GUI is a rabbit hole with no bottom.

## Stack

- Front end: TypeScript + Svelte 5 + D3 (treemap layout) +
  ``@lucide/svelte`` icons. No React — matches the ``front-ui``
  companion skill's stack.
- Back end: the ``os_helper`` library (and its CLIs) already covers
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
| M4 | "Prepare release" flow: pick a subtree, hash, describe, zip, upload — one keyboard shortcut chain. | Ties the whole helper together into a shippable artifact. |

## Non-goals (recorded so we do not drift)

- Not a file manager.
- Not a hosted SaaS.
- Not a substitute for the CLI in CI (the "what did I just do" panel
  emits shell scripts that CI can replay headless).

## Success metric

> A user who inherits a 500 GB scratch drive with 400k files can
> answer "what's here, what's duplicated, what's safe to zip and
> archive" in one afternoon, in one window, and leaves with a
> committable ``cleanup.sh``.

If we ship that, we win.

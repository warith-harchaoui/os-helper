---
name: os-helper
description: >-
  Local filesystem, system-introspection and utility toolbox — the foundation
  every other AI Helpers package builds on. Covers file/dir existence, globbing,
  copy/remove/mkdir, temp files and folders, zip, path splitting, SHA hashing of
  strings/files/folders, hardware and OS probing (CPU, RAM, GPU, Apple chip),
  worker-count sizing, wall/CPU/GPU timers, byte- and duration-formatting, URL
  liveness checks, file download, YAML/JSON config loading, and structured
  logging. Use when a task needs to inspect the machine ("how much RAM", "which
  GPU", "how many workers"), hash or compare files, build a safe temp path, walk
  or clean a directory tree, format sizes or durations, check whether a URL is
  alive, download a file, or load a config. Fires on `import os_helper as osh`,
  any `osh.` call, `os-helper-api`, `os-helper-mcp`, `os-helper-gui`, "Tree
  Radar", "treemap my disk". A library, with no command line. Do NOT use for audio,
  video, capture, download-site or document work — reach for the matching suite
  helper instead.
license: BSD-3-Clause
metadata:
  author: Warith Harchaoui
  package: os-helper
  suite: ai-helpers
  homepage: https://deraison.ai/ai-helpers
---

# os-helper — filesystem, hardware and utility foundation

`os-helper` is the AI Helpers suite's base layer: the module every other helper
imports for logging and file management. It is a *local* toolbox — paths, sizes,
hashes and hardware readings never leave the machine — reachable five ways
(library, two CLIs, HTTP API, MCP, and the Tree Radar GUI) so an agent can pick
whichever fits.

## Before anything: verify it is installed

```bash
os-helper --help                 # argparse CLI (always installed with the pkg)
python -c "import os_helper"     # library import check
```

If missing:

```bash
pip install os-helper                   # core: the library, no web stack
pip install 'os-helper[api]'            # + FastAPI HTTP surface (os-helper-api)
pip install 'os-helper[mcp]'            # + MCP tools over the same app (os-helper-mcp)
pip install 'os-helper[gui]'            # + Tree Radar disk-treemap GUI (os-helper-gui)
```

The core install is deliberately FastAPI-free: nine suite packages depend on
`import os_helper`, so the web stack is opt-in.

## What it does, and how to invoke it

| Intent | CLI | Library |
|--------|-----|---------|
| Machine / OS facts | `os-helper hardware`, `os-helper os` | `hardware_info`, `platform_name`, `gpus` |
| How many parallel workers to use | `os-helper workers` | `get_nb_workers` |
| Does this file / folder exist, how big | `os-helper exists`, `os-helper size` | `file_exists`, `dir_exists`, `size_file` |
| Walk / clean a tree | `os-helper glob`, `os-helper rm`, `os-helper rmdir` | `recursive_glob`, `remove_files`, `remove_directory` |
| Safe temp file / folder | `os-helper temp file`, `os-helper temp folder` | `temporary_filename`, `temporary_folder` |
| Hash a string / file / folder | `os-helper hash string|file|folder` | `hash_string`, `hashfile`, `hashfolder` |
| Split or join a path | `os-helper split`, `os-helper join` | `folder_name_ext`, `join` |
| Format bytes / parse-print a duration | `os-helper format-size`, `os-helper time2str` | `format_size`, `time2str`, `str2time` |
| Is this URL alive | `os-helper url-ok URL` | `is_working_url` |
| Download a file | `os-helper download URL` | `download_file` |
| Load a YAML/JSON/env config | `os-helper config` | `get_config` |
| Zip a folder | `os-helper zip DIR` | `zip_folder` |
| Browse disk usage visually | `os-helper gui` | — |

Quick examples:

```bash
os-helper hardware --json           # CPU model, cores, RAM, GPU vendor, Apple chip
os-helper workers                   # safe parallelism for this machine
os-helper hash file ./model.onnx    # content hash, for cache keys and integrity
os-helper glob ./data '*.wav'       # recursive glob
os-helper url-ok https://example.com
```

```python
import os_helper as osh

osh.init_logging("my-app", verbosity=1)
osh.info("starting")  # suite-wide structured logging
osh.check(osh.file_exists(p), msg=f"missing {p}")  # assert-with-a-message

with osh.temporary_folder() as tmp:  # cleaned up on exit
    out = osh.join(tmp, "clip.wav")
```

`osh.check(condition, msg=...)` is the suite's standard guard: it logs and
raises in one call. Every other helper uses `osh.info/warning/error` for logging
and `os_helper` for file management — follow that when writing suite code.

For the HTTP API, MCP tools and the Tree Radar GUI, read `references/surfaces.md`.
For the exhaustive, auditable trigger list, read `references/triggers.md`.

## Rules of thumb

- **Prefer the library inside Python, the CLI inside a shell.** The API and MCP
  surfaces exist for other processes and for agents without shell access.
- **Hardware questions are one call.** `hardware_info()` (or `os-helper hardware
  --json`) returns CPU model, logical/physical cores, RAM, available RAM, disk,
  GPU vendor and utilization, Apple chip name and unified memory in one shot —
  do not shell out to `sysctl` / `nvidia-smi` yourself.
- **Never hand-roll temp paths.** `temporary_filename()` / `temporary_folder()`
  are context managers that clean up; `/tmp/foo.wav` is not.
- **Hashing is for cache keys and integrity**, and `hashfolder` walks content,
  not mtimes — identical trees hash identically.
- **The API surface is the side-effect-free subset only.** It exposes hardware,
  hashing, ASCII, size/time formatting, URL checks and config loading — not
  `rm`, not `download`. That is deliberate; do not expect destructive routes.
- **Three calls touch the network, by design**: `download_file()`,
  `is_working_url()` and `get_user_ip()`. Everything else is strictly local.
- **After running, report the value you obtained** — do not re-run to confirm.

# os-helper skill — exhaustive trigger catalogue

Auditable list of the phrasings that should fire this skill. Keep it in sync
with the `description:` clause in `SKILL.md` — the description is what a host
model actually sees (and it is capped at 1024 characters), this file is the
human-reviewable superset.

## Fire (positive triggers)

**Machine and hardware questions**
- "how much RAM does this machine have", "how much free memory"
- "which GPU do I have", "is there a GPU", "is this an M-series Mac"
- "how many CPU cores", "what chip is this", "how many workers should I use"
- "how much disk space is left", "what OS / platform is this"
- "is this macOS / Linux / Windows" in code that must branch on it

**Files, folders and paths**
- "does this file exist", "how big is this file", "list every .wav under"
- "make this directory", "delete these files", "remove this folder"
- "copy this file", "zip this folder"
- "split this path into folder / name / extension", "join these path parts"
- "give me a temp file / scratch directory", "where should I put intermediates"
- "hide my home directory in this output / path"

**Hashing and identity**
- "hash this file / string / folder", "checksum", "fingerprint", "cache key"
- "did this folder change", "are these two trees identical"

**Formatting and time**
- "format these bytes", "1234567 bytes in human units"
- "turn 3725 seconds into 1h 2m 5s" and the inverse
- "timestamp for a filename"

**Network-touching utilities**
- "is this URL alive / reachable / 404"
- "download this file to disk"
- "what is my public IP"

**Config and logging**
- "load this YAML/JSON config", "read settings.yaml"
- "set up logging for this script", "how do I log in this suite"
- "add a guard / assertion with a message"

**Explicit tool and symbol mentions**
- `os-helper-api`, `os-helper-mcp`, `os-helper-gui` (there is no `os-helper` command)
- `import os_helper`, `import os_helper as osh`, `osh.<anything>`
- `hardware_info`, `get_nb_workers`, `recursive_glob`, `temporary_folder`,
  `hashfile`, `hashfolder`, `get_config`, `init_logging`, `check`, `format_size`
- "Tree Radar", "treemap my disk", "what is eating my disk"
- "install / run os-helper"

**Suite-internal work**
- Writing or reviewing code inside any `*-helper` repo that needs logging, a
  guard, a temp path, or file management — the suite convention is os-helper,
  not `print`, not `tempfile`, not bare `logging`.

## Do not fire (negative triggers)

- Audio transforms, conversion, separation → `audio-helper`
- Video conversion, frames, subtitles → `video-helper`
- Camera / microphone capture → `capture-helper`
- Downloading from YouTube or a podcast feed → `youtube-helper` / `podcast-helper`
- S3 or SFTP transfer → `bucket-helper` / `sftp-helper`
- Markdown → DOCX/PPTX/PDF → `md2star`
- Speech transcription / diarization → `vocal-helper`
- Picking an LLM or a vector index → `best-engine-ai-helper` / `ann-router`
- Generic Python questions with no filesystem, hardware or config angle
- `git` operations, package management, or shell scripting for its own sake

`download_file()` is the one overlap worth naming: use os-helper for a plain
URL → disk fetch, and `youtube-helper` / `podcast-helper` when the URL is a
media platform or an RSS feed and the metadata matters.

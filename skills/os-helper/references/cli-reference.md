# os-helper CLI reference

Both CLIs cover the same ground. `os-helper` (argparse) ships with the core
package and needs no extra dependency; `os-helper-click` (needs `[cli]`) is the
click twin with grouped help. Commands below are the argparse spelling; the
click names match except where noted.

## Command groups

### `os` — platform predicates
| Command | Prints |
|---|---|
| `os-helper os windows\|linux\|macos\|unix` | `true` / `false` for the running platform |
| `os-helper os info` | platform name |

### `hardware` — machine facts
| Command | Prints |
|---|---|
| `os-helper hardware` | human-readable CPU / RAM / disk / GPU report |
| `os-helper hardware --json` | the same as JSON (`hardware_info()`'s dict) |
| `os-helper system` | OS + architecture summary |
| `os-helper workers` | the safe parallel-worker count for this machine |
| `os-helper pid` | the current process id |

Click twin splits these finer: `os-helper-click cpu`, `gpu`, `info`, `system`,
`workers`, `pid`.

### `path` — paths without string surgery
| Command | Does |
|---|---|
| `os-helper path abs REL` | relative → absolute |
| `os-helper path rel ABS [--root R]` | absolute → relative |
| `os-helper path no-home P` | replace `$HOME` with `~` for safe display |
| `os-helper path join A B …` | join segments |
| `os-helper path split P` | → folder, basename, extension |

### `file` / `folder` — existence, size, listing, cleanup
| Command | Does |
|---|---|
| `os-helper exists PATH` | file exists? |
| `os-helper dir-exists PATH` | directory exists? |
| `os-helper size PATH` | file size in bytes |
| `os-helper glob DIR PATTERN` | recursive glob, one match per line |
| `os-helper describe DIR` | folder description (counts, total size) |
| `os-helper mkdir DIR` | create, parents included, idempotent |
| `os-helper rm PATH…` | remove files |
| `os-helper rmdir DIR` | remove a directory tree |
| `os-helper cp SRC DST` | copy a file, creating parents |
| `os-helper zip DIR [-o OUT]` | zip a folder |

### `temp` — scratch space that cleans up
| Command | Does |
|---|---|
| `os-helper temp file [--suffix .wav]` | print a fresh temp filename |
| `os-helper temp folder` | print a fresh temp directory |

In Python these are **context managers** (`with osh.temporary_folder() as d:`)
and remove themselves on exit — the CLI forms are for shell pipelines where the
caller owns cleanup.

### `hash` — content fingerprints
| Command | Does |
|---|---|
| `os-helper hash string "text"` | hash a string |
| `os-helper hash file PATH` | hash a file's bytes |
| `os-helper hash folder DIR` | hash a tree by content (not mtimes) |

### `str` / `misc` — formatting and small utilities
| Command | Does |
|---|---|
| `os-helper str ascii "Noël"` | ASCII-fold a string (slugs, filenames) |
| `os-helper str empty "  "` | is the string empty/whitespace? |
| `os-helper misc format-size 1234567` | → `1.2 MB` |
| `os-helper misc now` | timestamp string |
| `os-helper misc time2str 3725` | seconds → `1h 2m 5s` |
| `os-helper misc str2time "1h2m5s"` | the inverse |
| `os-helper misc url-ok URL` | is the URL alive? (network) |
| `os-helper misc ip` | public IP via an echo service (network) |

### `download`, `config`, `open`, `run`, `prof`, `gui`
| Command | Does |
|---|---|
| `os-helper download URL [-o OUT]` | fetch a URL to disk (network) |
| `os-helper config [--path P]` | load and print a YAML/JSON/env config |
| `os-helper open PATH` | open a file with the OS default app |
| `os-helper run "CMD"` | run a shell command through the suite's wrapper |
| `os-helper prof wall\|cpu\|gpu` | timer helpers |
| `os-helper gui [--port N]` | start the Tree Radar treemap server |

## Output contract

- Predicates print `true` / `false` and exit `0` either way; a *failure* exits
  non-zero with a logged message.
- `--json` is available on the reporting commands (`hardware`, `describe`,
  `config`); prefer it when parsing.
- Errors go through `osh.error`, so they are prefixed and land on stderr.

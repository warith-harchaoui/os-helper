# os-helper surfaces

Four doors onto the same toolbox. The core install deliberately carries none of
the web stack — nine suite packages depend on `import os_helper` and must not
pay for FastAPI.

## 1. Library (always available)

```python
import os_helper as osh
```

`osh` is the canonical alias across the suite. The three things every other
helper uses it for:

- **Logging** — `osh.init_logging(name, verbosity=…)`, then `osh.debug/info/
  warning/error/critical`. Never `print`, never a bare `logging.getLogger`.
- **Guards** — `osh.check(cond, msg="…")` logs and raises in one call.
- **File management** — `file_exists`, `dir_exists`, `make_directory`, `join`,
  `folder_name_ext`, `recursive_glob`, `temporary_filename`, `temporary_folder`,
  `copyfile`, `remove_files`, `remove_directory`, `zip_folder`.

Everything exported is listed in `os_helper.__all__`.

## 2. HTTP API — FastAPI (`[api]`)

```bash
pip install 'os-helper[api]'
os-helper-api                       # 127.0.0.1:8000, OpenAPI docs at /docs
```

| Method | Route | Returns |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/os` | platform predicates + name |
| GET | `/hardware` | the full `hardware_info()` dict |
| POST | `/hash/string` | hash of a posted string |
| POST | `/str/ascii` | ASCII-folded string |
| GET | `/misc/format-size` | human-readable byte size |
| GET | `/misc/now` | timestamp |
| GET | `/misc/url-ok` | URL liveness |
| POST | `/config` | parsed config |
| GET | `/gui`, `/api/tree` | Tree Radar page and its treemap data |

**The API exposes the side-effect-free subset on purpose.** There is no `rm`,
no `cp`, no `download` route: an HTTP surface that can delete the caller's disk
is not a surface worth shipping. Use the library or the CLI for mutations.

## 3. MCP — `fastapi-mcp` over the *same* app (`[mcp]`)

```bash
pip install 'os-helper[mcp]'
os-helper-mcp                       # same app, MCP mounted at /mcp
```

The MCP server is not a separate implementation: `os_helper.mcp` takes the
FastAPI app from `os_helper.api` and mounts `FastApiMCP` on it, so every tool is
a route and the two surfaces can never drift. One process serves both doors.

Register it with Claude Code:

```bash
claude mcp add os-helper --transport http http://127.0.0.1:8000/mcp
```

## 4. Tree Radar GUI (`[gui]`)

```bash
pip install 'os-helper[gui]'
os-helper-gui                       # http://127.0.0.1:8000/gui
```

A disk-usage treemap: point it at a directory and it renders what is eating the
space, locally, in the browser. The server binds `127.0.0.1` only — paths,
sizes and hashes never leave the machine. Reach for it when the user wants to
*see* where the disk went rather than read numbers.

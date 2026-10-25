# os-helper as an agent skill

`skills/os-helper/` packages `os-helper` as a **Claude Skill** *and* an **OpenCode
skill** — both ecosystems read the same `SKILL.md` (YAML frontmatter + Markdown
body + progressive-disclosure `references/`). Installing it lets an agent
discover os-helper and inspect the machine, manage files, hash, time and configure on the user's behalf, without the user opening a
terminal.

## Layout

```
skills/os-helper/
├── SKILL.md                  # name + trigger-rich description + instructions
└── references/
    ├── surfaces.md           # library, HTTP API, MCP, and the Tree Radar GUI
    └── triggers.md           # exhaustive, auditable trigger catalogue
```

Progressive disclosure, as the published skill standard prescribes: the YAML
frontmatter is always in the host model's context, `SKILL.md`'s body loads only
when the skill looks relevant, and `references/*.md` load only when a task
actually needs that depth. The `description` stays under the 1024-character cap;
the exhaustive trigger list lives in `references/triggers.md`.

## Install for Claude Code / Claude Desktop

Skills live under `~/.claude/skills/` (user) or `.claude/skills/` (project). To
track this repo's copy rather than duplicate it, symlink it:

```bash
ln -sfn "$PWD/skills/os-helper" ~/.claude/skills/os-helper
# per-project instead:
mkdir -p /path/to/project/.claude/skills
ln -sfn "$PWD/skills/os-helper" /path/to/project/.claude/skills/os-helper
```

## Install for OpenCode

OpenCode reads skills from `~/.opencode/skills/` (or `~/.config/opencode/skills/`):

```bash
mkdir -p ~/.opencode/skills
ln -sfn "$PWD/skills/os-helper" ~/.opencode/skills/os-helper
```

## Keeping triggers enforced

The host model only sees `SKILL.md`'s `description` before deciding to load the
skill, so every real trigger must be represented there — compressed into the
1024-character budget. `references/triggers.md` is the human-reviewable
superset, and it mirrors the repo-root `README.md` surface tables. When one changes, change the other.

No secrets live in this skill. os-helper is a local filesystem and system-
introspection toolbox: paths, sizes, hashes and hardware readings stay on the
machine. The three deliberate exceptions are documented in the repo's *The
Promise* section — `download_file()`, the URL-liveness check, and `get_user_ip()`
make outbound HTTP because fetching is their whole job.

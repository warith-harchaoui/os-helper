"""
OS Helper — optional "Tree Radar" treemap GUI.

Module summary
--------------
This module is an *optional* surface on top of the pure ``os_helper``
library. It serves a small, self-contained web dashboard — the "Tree
Radar" from ``GUI.md`` — that turns "what is on disk" into a single,
legible treemap:

- Each rectangle is a file or folder; its **area** is the file/subtree
  **size**, and its **color** encodes one of three modes:
  - **age** (recent vs. stale, from each file's mtime),
  - **hash-dedupe** (files that share a content hash form a cluster,
    colored so duplicates stand out), or
  - **type family** (code / data / media / archive / other).
- Hovering a rectangle reveals its absolute path, human-readable size
  (via :func:`os_helper.format_size`), last-modified timestamp and — on
  demand — its RIPEMD-160 / BLAKE2b content hash (via
  :func:`os_helper.hashfile`).

Why it exists
-------------
The CLI handles "one path, one predicate at a time" well. A GUI must go
further, so this one shows the *whole* tree at a glance. It is a thin
client: **all** the read/compute work is delegated to the existing
``os_helper`` helpers (``os.walk`` size collection, ``format_size``,
``hashfile``), never reinvented here.

What it consumes / produces
---------------------------
- Consumes: a local directory root (a path on this machine).
- Produces: a locally-served HTML page (``GET /gui``) and a JSON tree
  (``GET /api/tree``). Nothing is uploaded; no telemetry; no account.

Lean-import contract
--------------------
``import os_helper as osh`` must stay free of FastAPI/uvicorn. FastAPI is
therefore imported *inside* :func:`create_app` / :func:`run`, never at
module top level, and the whole GUI lives behind the optional
``os-helper[gui]`` extra. Importing *this* module is cheap; it only pulls
FastAPI when you actually build or run the app.

Usage example
-------------
>>> # Requires the optional extra:  pip install "os-helper[gui]"
>>> from os_helper.gui import run
>>> run(root="~/Downloads", port=8017)  # doctest: +SKIP

Author
------
Warith Harchaoui, Ph.D. — https://linkedin.com/in/warith-harchaoui/
"""

# Postpone annotation evaluation so FastAPI types can be referenced in
# signatures without importing FastAPI at module import time.
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, TypedDict

# Reuse the library's own helpers — do NOT reinvent size/hash/format logic.
# These are all pure-Python and dependency-light, so importing them keeps the
# GUI module cheap to import (the FastAPI cost is deferred to create_app/run).
from . import error, format_size, hashfile, info, warning

# FastAPI is an *optional* dependency (the ``gui`` extra). We only import it
# for type-checkers here; the runtime import happens lazily in create_app().
if TYPE_CHECKING:  # pragma: no cover — typing only, never runs
    from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Type-family classification — used for the "type family" color mode.
# ---------------------------------------------------------------------------

# Map lower-cased file extensions to a coarse "family" the treemap colors by.
# Kept deliberately small and opinionated: the goal is a glanceable palette,
# not an exhaustive MIME table. Anything unlisted falls into "other".
_TYPE_FAMILIES: dict[str, str] = {
    # Source code and scripts.
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".c": "code",
    ".h": "code",
    ".cpp": "code",
    ".rs": "code",
    ".go": "code",
    ".java": "code",
    ".sh": "code",
    ".rb": "code",
    # Structured / tabular data and text.
    ".json": "data",
    ".yaml": "data",
    ".yml": "data",
    ".csv": "data",
    ".tsv": "data",
    ".txt": "data",
    ".md": "data",
    ".xml": "data",
    ".parquet": "data",
    # Media: images, audio, video.
    ".png": "media",
    ".jpg": "media",
    ".jpeg": "media",
    ".gif": "media",
    ".svg": "media",
    ".mp3": "media",
    ".wav": "media",
    ".flac": "media",
    ".mp4": "media",
    ".mov": "media",
    ".mkv": "media",
    # Archives / compressed bundles.
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".bz2": "archive",
    ".xz": "archive",
    ".7z": "archive",
    ".rar": "archive",
}


def _type_family(name: str) -> str:
    """Classify a filename into a coarse type family for treemap coloring.

    Parameters
    ----------
    name : str
        A file's base name (extension is read from it, case-insensitively).

    Returns
    -------
    str
        One of ``"code"``, ``"data"``, ``"media"``, ``"archive"`` or
        ``"other"`` — the family used to pick a color in "type" mode.

    Examples
    --------
    >>> _type_family("main.PY")
    'code'
    >>> _type_family("archive.tar.gz")
    'archive'
    >>> _type_family("noext")
    'other'
    """
    # os.path.splitext keeps only the final extension (".gz" for "x.tar.gz"),
    # which is the right granularity for a coarse family bucket.
    _, ext = os.path.splitext(name)
    # Look up the lower-cased extension; unknown/extensionless files are "other".
    return _TYPE_FAMILIES.get(ext.lower(), "other")


# ---------------------------------------------------------------------------
# The JSON shape returned to the browser. Declaring it as a TypedDict keeps
# the contract explicit (CODING.md rule 3) and documents the tree schema.
# ---------------------------------------------------------------------------


class TreeNode(TypedDict, total=False):
    """One node of the directory tree sent to the browser as JSON.

    A node is either a file (no ``children``) or a directory (with a
    ``children`` list). Sizes are in bytes; ``size_h`` is the pre-formatted
    human-readable string so the front-end never re-implements
    :func:`os_helper.format_size`.
    """

    name: str  # base name (leaf display label)
    path: str  # absolute path on this machine
    size: int  # size in bytes (own size for files; subtree total for dirs)
    size_h: str  # human-readable size via os_helper.format_size
    mtime: float  # last-modified time, seconds since the epoch
    is_dir: bool  # True for directories, False for files
    family: str  # type family ("code" / "data" / ... ) — files only
    children: list[TreeNode]  # present on directories only


def _scan_tree(
    root: str,
    max_depth: int,
    max_entries: int,
    _depth: int = 0,
    _budget: list[int] | None = None,
) -> TreeNode:
    """Walk a directory into a nested :class:`TreeNode` tree of sizes.

    This is the treemap's data source. It mirrors the ``os.walk``-based
    size collection used elsewhere in :mod:`os_helper.misc_utils`, but
    returns a *nested* structure (rather than a flat mapping) because the
    treemap needs the hierarchy. File sizes come from ``os.stat`` and are
    rendered with :func:`os_helper.format_size` so the human-readable
    string is computed exactly once, server-side.

    Parameters
    ----------
    root : str
        Absolute path of the directory (or file) to scan.
    max_depth : int
        Maximum recursion depth. Directories deeper than this are summarized
        by their own on-disk entry only (their children are omitted) to keep
        the payload bounded on very deep trees.
    max_entries : int
        Global cap on how many filesystem entries are visited across the whole
        scan. Protects the server from pathological (400k-file) trees.
    _depth : int, optional
        Internal recursion depth counter. Do not pass this yourself.
    _budget : list of int, optional
        Internal single-element mutable counter tracking the remaining entry
        budget across the recursion. Do not pass this yourself.

    Returns
    -------
    TreeNode
        The root node, with nested ``children`` for directories.

    Notes
    -----
    Hidden entries (names starting with ``"."``) are skipped, matching the
    convention in :func:`os_helper.folder_description`. Unreadable entries
    (permission errors, broken symlinks) are logged via ``osh.warning`` and
    skipped rather than aborting the whole scan.
    """
    # A single-element list acts as a shared, mutable counter across the
    # recursion so the entry cap is truly global, not per-directory.
    if _budget is None:
        _budget = [max_entries]

    # Base name for display; fall back to the full path for filesystem roots
    # like "/" whose basename is empty.
    name = os.path.basename(root.rstrip(os.sep)) or root

    # Leaf case: a file. Stat it once for size + mtime; classify its family.
    if not os.path.isdir(root):
        try:
            st = os.stat(root)
        except OSError as exc:
            # Broken symlink or vanished file: report it, size it as zero.
            warning(f"Tree Radar: cannot stat file '{root}': {exc}")
            return {
                "name": name,
                "path": root,
                "size": 0,
                "size_h": format_size(0),
                "mtime": 0.0,
                "is_dir": False,
                "family": _type_family(name),
            }
        size = int(st.st_size)
        return {
            "name": name,
            "path": root,
            "size": size,
            "size_h": format_size(size),
            "mtime": float(st.st_mtime),
            "is_dir": False,
            "family": _type_family(name),
        }

    # Directory case: accumulate children and roll their sizes up.
    children: list[TreeNode] = []
    total = 0
    # Directory mtime is still useful for "age" coloring of folder rectangles.
    try:
        dir_mtime = float(os.stat(root).st_mtime)
    except OSError:
        dir_mtime = 0.0

    # Beyond max_depth we stop descending: return the directory node without
    # children so deep trees don't explode the JSON payload.
    if _depth >= max_depth:
        return {
            "name": name,
            "path": root,
            "size": 0,
            "size_h": format_size(0),
            "mtime": dir_mtime,
            "is_dir": True,
            "children": [],
        }

    # List the directory once; permission errors are logged and skipped so a
    # single unreadable folder never aborts the whole scan.
    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name)
    except OSError as exc:
        warning(f"Tree Radar: cannot list directory '{root}': {exc}")
        entries = []

    for entry in entries:
        # Stop entirely once the global entry budget is exhausted.
        if _budget[0] <= 0:
            break
        # Skip dotfiles/dotdirs: editor/OS metadata, not user content.
        if entry.name.startswith("."):
            continue
        # Charge one unit of the global budget per entry visited.
        _budget[0] -= 1
        # Recurse: directories descend, files return a leaf node. We pass the
        # shared depth + budget so limits are enforced across the whole tree.
        child = _scan_tree(
            entry.path,
            max_depth=max_depth,
            max_entries=max_entries,
            _depth=_depth + 1,
            _budget=_budget,
        )
        children.append(child)
        total += child["size"]

    return {
        "name": name,
        "path": root,
        "size": total,
        "size_h": format_size(total),
        "mtime": dir_mtime,
        "is_dir": True,
        "children": children,
    }


def _dedupe_groups(node: TreeNode, groups: dict[str, list[str]] | None = None) -> dict[str, list[str]]:
    """Group file paths by shared content hash (the Dedupe Lens data).

    Walks an already-scanned :class:`TreeNode` tree, hashes every file with
    :func:`os_helper.hashfile`, and returns a mapping ``hash -> [paths]``
    limited to hashes that occur more than once (i.e. actual duplicates).
    This feeds the treemap's "hash-dedupe" color mode and the Dedupe Lens.

    Parameters
    ----------
    node : TreeNode
        A node produced by :func:`_scan_tree` (usually the root).
    groups : dict, optional
        Internal accumulator mapping content hash to the list of paths seen
        with that hash. Do not pass this yourself.

    Returns
    -------
    dict of str to list of str
        Mapping from content hash to the ≥2 paths sharing it. Unique files
        are omitted, so an empty dict means "no duplicates found".

    Notes
    -----
    Hashing reads file content, so this is the expensive path. It is only
    invoked when the caller asks for dedupe coloring (``?dedupe=1``), never on
    the default tree fetch.
    """
    # First (top-level) call seeds the accumulator; recursion reuses it so all
    # files across the tree land in the same hash buckets.
    if groups is None:
        groups = {}

    # Directory: recurse into children, nothing to hash for the folder itself.
    if node.get("is_dir"):
        for child in node.get("children", []):
            _dedupe_groups(child, groups)
        return groups

    # File: hash its content and bucket the path under that digest. hashfile
    # already handles the RIPEMD-160 / BLAKE2b fallback for us.
    path = node["path"]
    try:
        digest = hashfile(path, hash_content=True)
    except OSError as exc:
        # Unreadable file: skip it rather than aborting the whole dedupe pass.
        warning(f"Tree Radar: cannot hash '{path}' for dedupe: {exc}")
        return groups
    groups.setdefault(digest, []).append(path)
    return groups


def build_tree_payload(
    root: str,
    max_depth: int = 12,
    max_entries: int = 20000,
    dedupe: bool = False,
) -> dict[str, Any]:
    """Build the full JSON payload served by ``GET /api/tree``.

    This is the backend entry point behind the data endpoint. It scans the
    tree (sizes + mtimes + families) and, when ``dedupe`` is set, also
    computes content-hash duplicate groups.

    Parameters
    ----------
    root : str
        Directory to scan. ``~`` is expanded and the path is made absolute.
    max_depth : int, optional
        Maximum recursion depth (default 12).
    max_entries : int, optional
        Global cap on entries visited (default 20000).
    dedupe : bool, optional
        If True, also hash every file and include a ``dedupe`` mapping of
        duplicate clusters. Defaults to False (cheap, no content reads).

    Returns
    -------
    dict
        ``{"root": <abs path>, "tree": <TreeNode>, "dedupe": {hash: [paths]}}``.

    Raises
    ------
    NotADirectoryError
        If ``root`` does not resolve to an existing directory.
    """
    # Normalize the requested root: expand ~ and resolve to an absolute path so
    # the payload always carries unambiguous, machine-local paths.
    abs_root = os.path.abspath(os.path.expanduser(root))
    # Fail loudly (the route turns this into an HTTP 400) if the path is not a
    # real directory — the treemap only makes sense on a folder.
    if not os.path.isdir(abs_root):
        raise NotADirectoryError(f"Not a directory: {abs_root}")

    info(f"Tree Radar: scanning '{abs_root}' (max_depth={max_depth}, dedupe={dedupe})")
    # Walk the tree into a nested node structure of sizes/mtimes/families.
    tree = _scan_tree(abs_root, max_depth=max_depth, max_entries=max_entries)

    # Only pay for content hashing when the caller actually asked for it.
    dedupe_map: dict[str, list[str]] = {}
    if dedupe:
        all_groups = _dedupe_groups(tree)
        # Keep only real duplicate clusters (a hash seen on 2+ distinct paths).
        dedupe_map = {h: paths for h, paths in all_groups.items() if len(paths) > 1}

    return {"root": abs_root, "tree": tree, "dedupe": dedupe_map}


# ---------------------------------------------------------------------------
# The single-page front-end. Self-contained HTML + vanilla JS; the only
# client dependency is D3 loaded from a CDN (no build step, per GUI.md).
# ---------------------------------------------------------------------------

# The page is a plain module-level constant so serving it is a zero-cost
# string response. It renders a squarified treemap via d3.treemap, wires the
# three color modes (age / dedupe / type), and shows a hover tooltip. All
# data comes from GET /api/tree; nothing here phones home.
_INDEX_HTML: str = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>OS Helper — Tree Radar</title>
<!-- D3 is the only client dependency, loaded from a CDN (no build step). -->
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; font-family: system-ui, -apple-system, sans-serif; }
  header { padding: 10px 14px; border-bottom: 1px solid #8884; display: flex;
           gap: 10px; align-items: center; flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0 12px 0 0; }
  input[type=text] { padding: 6px 8px; min-width: 320px; }
  button, select { padding: 6px 10px; }
  #status { font-size: 12px; opacity: 0.7; margin-left: auto; }
  #chart { width: 100vw; height: calc(100vh - 52px); }
  .node rect { stroke: #0004; stroke-width: 0.5px; cursor: pointer; }
  .node text { font-size: 10px; pointer-events: none; fill: #000; }
  #tip { position: fixed; pointer-events: none; background: #000d; color: #fff;
         padding: 6px 8px; border-radius: 4px; font-size: 12px; display: none;
         max-width: 480px; z-index: 10; }
</style>
</head>
<body>
<header>
  <h1>Tree Radar</h1>
  <!-- Root folder to scan. Defaults to whatever the server was launched with. -->
  <input type="text" id="root" placeholder="/absolute/path/to/folder" />
  <button id="scan">Scan</button>
  <!-- Color mode: which signal the rectangle color encodes. -->
  <label>Color:
    <select id="mode">
      <option value="age">age</option>
      <option value="dedupe">hash-dedupe</option>
      <option value="type">type family</option>
    </select>
  </label>
  <span id="status">idle</span>
</header>
<div id="chart"></div>
<div id="tip"></div>
<script>
// ---- Tree Radar front-end (vanilla JS + D3) ----------------------------
// All state is local to the browser. We fetch JSON from /api/tree and lay it
// out as a squarified treemap; color encodes age / dedupe / type per the
// selected mode. Your paths and hashes never leave this machine.

const statusEl = document.getElementById("status");   // small status line
const rootEl = document.getElementById("root");       // root-path input
const modeEl = document.getElementById("mode");       // color-mode selector
const tip = document.getElementById("tip");           // hover tooltip

let lastData = null;   // last payload from /api/tree, cached for re-color

// Pre-fill the root input with the server's launch root (injected below).
rootEl.value = window.__OSH_ROOT__ || "";

// Coarse type-family palette. Colorblind-ish distinct hues; shapes are all
// rectangles so this is the one place color carries meaning (see GUI.md note
// on colorblind-safety — a pattern fallback is a future milestone).
const FAMILY_COLORS = {
  code: "#4e79a7", data: "#59a14f", media: "#e15759",
  archive: "#f28e2b", other: "#9c9c9c",
};

// Fetch the tree JSON for a root path. `dedupe` triggers server-side hashing.
async function fetchTree(root, dedupe) {
  statusEl.textContent = "scanning...";
  const url = "/api/tree?root=" + encodeURIComponent(root) +
              (dedupe ? "&dedupe=1" : "");
  const resp = await fetch(url);
  if (!resp.ok) {
    // Surface backend errors (e.g. "not a directory") in the status line.
    const msg = await resp.text();
    statusEl.textContent = "error: " + msg;
    throw new Error(msg);
  }
  return await resp.json();
}

// Map a file's mtime to a blue(recent)->red(stale) color across the range of
// mtimes actually present in the current tree, so the scale auto-fits.
function ageColorScale(root) {
  const times = [];
  // Collect every leaf mtime to establish min/max for the scale.
  (function walk(n) {
    if (n.children) n.children.forEach(walk);
    else if (n.data && n.data.mtime) times.push(n.data.mtime);
  })(root);
  const min = d3.min(times) || 0, max = d3.max(times) || 1;
  // d3 interpolateRdYlBu: 0 -> red (old), 1 -> blue (recent). We invert the
  // domain so recent files (large mtime) map to blue.
  const scale = d3.scaleLinear().domain([min, max]).range([0, 1]);
  return (mtime) => d3.interpolateRdYlBu(scale(mtime || min));
}

// Decide a rectangle's fill for the current color mode.
function colorFor(leaf, mode, ageScale, dupSet) {
  const d = leaf.data;
  if (mode === "type") return FAMILY_COLORS[d.family || "other"];
  if (mode === "dedupe") {
    // Gold = part of a duplicate cluster; grey = unique. dupSet holds every
    // path that shares its content hash with at least one other file.
    return dupSet.has(d.path) ? "#d4af37" : "#9c9c9c";
  }
  // Default: age coloring.
  return ageScale(d.mtime);
}

// Render the treemap for the cached payload + current color mode.
function render() {
  if (!lastData) return;
  const chart = document.getElementById("chart");
  const w = chart.clientWidth, h = chart.clientHeight;

  // Build the D3 hierarchy; sum leaf sizes so parent areas roll up correctly.
  const root = d3.hierarchy(lastData.tree)
    .sum((d) => (d.children ? 0 : d.size))
    .sort((a, b) => b.value - a.value);

  // Squarified treemap layout with a little padding for legibility.
  d3.treemap().size([w, h]).paddingInner(1)(root);

  const mode = modeEl.value;
  const ageScale = ageColorScale(root);
  // Flatten the server's dedupe map (hash -> [paths]) into a fast lookup set.
  const dupSet = new Set();
  Object.values(lastData.dedupe || {}).forEach((paths) =>
    paths.forEach((p) => dupSet.add(p)));

  // Clear and redraw the SVG from scratch — simplest correct approach for a
  // full re-layout on every scan / mode change.
  const svg = d3.select("#chart").html("")
    .append("svg").attr("width", w).attr("height", h);

  // One <g> per leaf rectangle.
  const leaves = root.leaves();
  const g = svg.selectAll("g").data(leaves).enter()
    .append("g").attr("class", "node")
    .attr("transform", (d) => `translate(${d.x0},${d.y0})`);

  g.append("rect")
    .attr("width", (d) => Math.max(0, d.x1 - d.x0))
    .attr("height", (d) => Math.max(0, d.y1 - d.y0))
    .attr("fill", (d) => colorFor(d, mode, ageScale, dupSet))
    // Hover: show the full detail tooltip (path, size, mtime, family).
    .on("mousemove", (event, d) => {
      const dt = new Date((d.data.mtime || 0) * 1000);
      tip.style.display = "block";
      tip.style.left = (event.clientX + 12) + "px";
      tip.style.top = (event.clientY + 12) + "px";
      tip.innerHTML =
        "<b>" + d.data.path + "</b><br>" +
        d.data.size_h + " &middot; " + (d.data.family || "dir") + "<br>" +
        "modified " + dt.toLocaleString();
    })
    .on("mouseout", () => { tip.style.display = "none"; });

  // Label only rectangles large enough to fit readable text.
  g.filter((d) => (d.x1 - d.x0) > 40 && (d.y1 - d.y0) > 14)
    .append("text").attr("x", 3).attr("y", 12)
    .text((d) => d.data.name);

  statusEl.textContent =
    "root: " + lastData.root + "  (" + leaves.length + " files shown)";
}

// Kick off a scan for the current root + mode, then render.
async function scan() {
  const root = rootEl.value.trim();
  if (!root) { statusEl.textContent = "enter a folder path"; return; }
  // Dedupe coloring needs the (expensive) server-side hash pass.
  const wantDedupe = modeEl.value === "dedupe";
  try {
    lastData = await fetchTree(root, wantDedupe);
    render();
  } catch (e) { /* status line already shows the error */ }
}

// Wire the controls: Scan button, Enter in the input, and mode changes.
document.getElementById("scan").addEventListener("click", scan);
rootEl.addEventListener("keydown", (e) => { if (e.key === "Enter") scan(); });
modeEl.addEventListener("change", () => {
  // Switching to dedupe requires a fresh fetch (needs hashes); other modes
  // just recolor the cached tree instantly.
  if (modeEl.value === "dedupe") scan(); else render();
});
window.addEventListener("resize", render);

// Auto-scan the launch root on first load so the page is useful immediately.
if (rootEl.value) scan();
</script>
</body>
</html>
"""


def create_app(default_root: str | None = None) -> FastAPI:
    """Build the FastAPI application serving the Tree Radar GUI.

    FastAPI is imported *here*, not at module top level, so that merely
    importing :mod:`os_helper` (or even this module) never pulls the web
    stack. The web dependencies live behind the ``os-helper[gui]`` extra.

    Parameters
    ----------
    default_root : str, optional
        Folder to pre-fill in the page and auto-scan on load. Defaults to the
        current working directory when not given.

    Returns
    -------
    fastapi.FastAPI
        The configured application, exposing ``GET /gui`` (the page) and
        ``GET /api/tree`` (the JSON data endpoint).

    Raises
    ------
    ImportError
        If FastAPI is not installed (i.e. the ``gui`` extra is missing),
        with a message pointing at ``pip install "os-helper[gui]"``.
    """
    # Lazy, guarded import: this is the single place the optional web stack is
    # required. A clear ImportError beats an opaque ModuleNotFoundError.
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError as exc:  # pragma: no cover — exercised only without extra
        error("Tree Radar GUI requires the optional 'gui' extra (FastAPI/uvicorn).")
        raise ImportError(
            "The Tree Radar GUI needs FastAPI/uvicorn. Install the extra:\n"
            '    pip install "os-helper[gui]"'
        ) from exc

    # Resolve the launch root once so both the page and default scans agree.
    launch_root = os.path.abspath(os.path.expanduser(default_root or os.getcwd()))

    app = FastAPI(
        title="OS Helper — Tree Radar",
        description="Local-first treemap disk dashboard. Nothing leaves your machine.",
    )

    @app.get("/gui", response_class=HTMLResponse)
    def gui_page() -> HTMLResponse:
        """Serve the self-contained Tree Radar HTML page.

        Returns
        -------
        fastapi.responses.HTMLResponse
            The single-page app, with the launch root injected so the page
            auto-scans a sensible folder on first load.
        """
        # Inject the server's launch root into the page as a JS global so the
        # input is pre-filled and the first auto-scan targets a real folder.
        # Use json.dumps to produce a *valid JS string literal*: it escapes
        # backslashes and quotes correctly, so Windows paths like
        # ``C:\Users\...`` embed safely (``C:\\Users\\...``) rather than
        # breaking the script.
        root_literal = json.dumps(launch_root)
        page = _INDEX_HTML.replace(
            'window.__OSH_ROOT__ || ""',
            f'{root_literal} || ""',
        )
        return HTMLResponse(content=page)

    @app.get("/api/tree", response_class=JSONResponse)
    def api_tree(
        root: str = Query(default=None, description="Folder to scan."),
        depth: int = Query(default=12, ge=1, le=64),
        dedupe: int = Query(default=0, ge=0, le=1),
    ) -> JSONResponse:
        """Return the directory tree as JSON for the treemap.

        Parameters
        ----------
        root : str, optional
            Folder to scan; defaults to the server's launch root.
        depth : int, optional
            Maximum recursion depth (1–64, default 12).
        dedupe : int, optional
            When ``1``, also hash files and include duplicate clusters.

        Returns
        -------
        fastapi.responses.JSONResponse
            The payload from :func:`build_tree_payload`.

        Raises
        ------
        fastapi.HTTPException
            400 when the requested root is not an existing directory.
        """
        # Fall back to the launch root when the query omits ?root=.
        target = root or launch_root
        try:
            payload = build_tree_payload(target, max_depth=depth, dedupe=bool(dedupe))
        except NotADirectoryError as exc:
            # Turn the domain error into a clean 400 the front-end can display.
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse(content=payload)

    return app


def run(
    root: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8017,
) -> None:
    """Launch the Tree Radar GUI with uvicorn (blocking).

    Binds to loopback by default so the dashboard is reachable only from this
    machine — consistent with the local-first promise.

    Parameters
    ----------
    root : str, optional
        Folder to pre-fill and auto-scan. Defaults to the current directory.
    host : str, optional
        Interface to bind. Defaults to ``"127.0.0.1"`` (localhost only).
    port : int, optional
        TCP port to serve on. Defaults to ``8017``.

    Raises
    ------
    ImportError
        If the ``gui`` extra (FastAPI/uvicorn) is not installed.

    Notes
    -----
    This call blocks until the server is stopped (Ctrl-C).
    """
    # uvicorn is part of the optional extra; import it lazily with a friendly
    # error so the lean core import is never burdened with the web server.
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover — exercised only without extra
        error("Tree Radar GUI requires uvicorn (install the 'gui' extra).")
        raise ImportError(
            "The Tree Radar GUI needs uvicorn. Install the extra:\n"
            '    pip install "os-helper[gui]"'
        ) from exc

    # Build the app bound to the chosen launch root, then serve it.
    app = create_app(default_root=root)
    info(f"Tree Radar: serving http://{host}:{port}/gui  (root: {root or os.getcwd()})")
    uvicorn.run(app, host=host, port=port)


def _cli_main(argv: list[str] | None = None) -> int:
    """Console-script entry point for the ``os-helper-gui`` command.

    A tiny argparse wrapper around :func:`run` so the GUI can be launched
    directly from the shell once the ``gui`` extra is installed.

    Parameters
    ----------
    argv : list of str, optional
        Arguments to parse; defaults to ``sys.argv[1:]`` when None.

    Returns
    -------
    int
        Process exit code (0 on success).
    """
    # argparse lives in the stdlib, so this stays importable without the extra;
    # the FastAPI/uvicorn requirement only bites inside run().
    import argparse

    parser = argparse.ArgumentParser(
        prog="os-helper-gui",
        description="Launch the local Tree Radar treemap disk dashboard.",
    )
    parser.add_argument(
        "--root", default=None, help="Folder to pre-fill and scan (default: current directory)."
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind interface (default: 127.0.0.1, localhost only)."
    )
    parser.add_argument("--port", type=int, default=8017, help="Port to serve on (default: 8017).")
    ns = parser.parse_args(argv)

    # Delegate to run(); it raises a friendly ImportError if the extra is absent.
    run(root=ns.root, host=ns.host, port=ns.port)
    return 0


if __name__ == "__main__":  # pragma: no cover — module run directly
    raise SystemExit(_cli_main())

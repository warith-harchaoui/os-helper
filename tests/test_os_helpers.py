import json
import os
import time

import pytest

from os_helper import (
    asciistring,
    copyfile,
    cpu_timer,
    dir_exists,
    emptystring,
    file_exists,
    folder_description,
    get_config,
    gpu_timer,
    hashfolder,
    join,
    make_directory,
    now_string,
    recursive_glob,
    relative2absolute_path,
    remove_directory,
    remove_files,
    temporary_filename,
    temporary_folder,
    temporary_remote_file,
    tic,
    toc,
    verbosity,
    wall_timer,
    zip_folder,
)

# Define a test folder to isolate test artifacts
TEST_FOLDER = os.path.join(os.getcwd(), "os_helper_test_folder")
os.makedirs(TEST_FOLDER, exist_ok=True)  # Ensure the folder exists


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """
    Fixture to handle setup and teardown for all tests.

    - Creates the test environment before running the tests.
    - Cleans up all files and folders in `TEST_FOLDER` after tests complete.
    """
    yield  # Let the tests run
    # Cleanup process after tests
    for root, dirs, files in os.walk(TEST_FOLDER, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))  # Remove files
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))  # Remove directories
    os.rmdir(TEST_FOLDER)  # Remove the test folder itself


def test_verbosity_get_and_set():
    """
    `verbosity` should act as both a getter (no arg) and a setter (int arg),
    matching how the README/EXAMPLES use it.
    """
    previous = verbosity()
    try:
        assert verbosity(2) == 2  # DEBUG
        assert verbosity() == 2
        assert verbosity(0) == 0  # WARNING
        assert verbosity(-1) == -1  # ERROR
        assert verbosity(3) == 2  # clamped to DEBUG
        assert verbosity(-5) == -2  # clamped to CRITICAL
    finally:
        verbosity(previous)


def test_emptystring():
    """
    Test the `emptystring` function.

    - Verifies it correctly identifies empty strings and None as empty.
    - Verifies it returns False for non-empty strings.
    """
    assert emptystring("") is True  # An empty string should return True
    assert emptystring(None) is True  # None should return True
    assert emptystring("Non-empty") is False  # A non-empty string should return False


def test_now_string():
    """
    Test the `now_string` function.

    - Verifies it generates timestamps in correct formats.
    - Checks that "log" format contains slashes.
    - Checks that "filename" format excludes characters like colons.
    """
    log_format = now_string("log")  # Generate log-format timestamp
    filename_format = now_string("filename")  # Generate filename-safe timestamp
    assert "/" in log_format  # Log format should include "/"
    assert "-" in filename_format  # Filename format should include "-"
    assert ":" not in filename_format  # Filename format should exclude ":"


def test_file_exists():
    """
    Test the `file_exists` function.

    - Creates a temporary file and verifies its existence.
    - Verifies it correctly identifies non-existent files.
    """
    temp_file = os.path.join(TEST_FOLDER, "test_file_exists.txt")
    with open(temp_file, "w") as f:
        f.write("Content")  # Create a test file
    assert file_exists(temp_file) is True  # Verify the file exists
    assert file_exists("non_existent_file.txt") is False  # Verify a non-existent file returns False


def test_dir_exists():
    """
    Test the `dir_exists` function.

    - Creates a directory and verifies its existence.
    - Verifies it correctly identifies non-existent directories.
    - Verifies the `check_empty` parameter functionality.
    """
    test_dir = os.path.join(TEST_FOLDER, "test_dir_exists")
    os.makedirs(test_dir)  # Create the test directory
    assert dir_exists(test_dir) is True  # Directory should exist
    assert dir_exists(test_dir, check_empty=True) is False  # Directory should be empty
    sub_dir = join(test_dir, "sub_folder")  # Create a non-existent subdirectory path
    assert dir_exists(sub_dir) is False  # Non-existent directory should return False


def test_relative2absolute_path():
    """
    Test the `relative2absolute_path` function.

    - Converts a relative path to an absolute path and verifies correctness.
    - Ensures relative paths remain unaffected.
    """
    relative_path = os.path.relpath(TEST_FOLDER)  # Get a relative path for testing
    absolute_path = relative2absolute_path(relative_path)  # Convert to absolute path
    assert os.path.isabs(absolute_path), (
        f"Path is not absolute: {absolute_path}"
    )  # Verify the result is absolute
    assert not os.path.isabs(relative_path), (
        f"Path is not relative: {relative_path}"
    )  # Ensure the input is relative


def test_asciistring():
    """
    Test the `asciistring` function.

    - Verifies it converts non-ASCII characters to ASCII equivalents.
    - Verifies it replaces special characters with the replacement character.
    """
    assert (
        asciistring("Café-Con-Leche!") == "cafe-con-leche"
    )  # Replace accented and special characters
    assert asciistring("Special#File$2024", lower=False) == "Special-File-2024"  # Preserve case
    assert asciistring("Café@2024.txt") == "cafe-2024-txt"  # Replace "@" with a hyphen


def test_zip_folder():
    """
    Test the `zip_folder` function.

    - Creates a test folder with files, zips it, and verifies the zip file exists.
    """
    test_dir = os.path.join(TEST_FOLDER, "test_zip_folder")
    os.makedirs(test_dir)  # Create the test directory
    # Create test files
    file1 = join(test_dir, "file1.txt")
    file2 = join(test_dir, "file2.txt")
    with open(file1, "w") as f1, open(file2, "w") as f2:
        f1.write("File 1 content")
        f2.write("File 2 content")
    zip_file = os.path.join(TEST_FOLDER, "output.zip")  # Define zip file path
    zip_folder(test_dir, zip_file_path=zip_file)  # Zip the folder
    assert file_exists(zip_file)  # Verify the zip file exists


def test_recursive_glob():
    """
    Test the `recursive_glob` function.

    - Creates a directory with files matching a pattern and verifies the function finds them.
    """
    test_dir = os.path.join(TEST_FOLDER, "test_recursive_glob")
    os.makedirs(test_dir)  # Create the test directory
    # Create test files
    file1 = join(test_dir, "file1.txt")
    file2 = join(test_dir, "file2.txt")
    with open(file1, "w") as f1, open(file2, "w") as f2:
        f1.write("File 1 content")
        f2.write("File 2 content")
    files = recursive_glob(test_dir, "*.txt")  # Search for files matching pattern
    assert len(files) == 2  # Verify two files are found
    assert file1 in files  # Verify specific file is found
    assert file2 in files  # Verify specific file is found


def test_relative2absolute_path_checkpath_raises():
    """
    `relative2absolute_path(checkpath=True)` must raise FileNotFoundError when
    the resolved path does not exist (previously silently returned the path).
    """
    missing = os.path.join(TEST_FOLDER, "definitely_does_not_exist.xyz")
    with pytest.raises(FileNotFoundError):
        relative2absolute_path(missing, checkpath=True)


def test_copyfile_propagates_failure():
    """
    `copyfile` must raise (not just log) when shutil cannot perform the copy.
    Here we force failure by pointing the destination at a directory that
    doesn't exist.
    """
    src = os.path.join(TEST_FOLDER, "copyfile_src.txt")
    with open(src, "w") as f:
        f.write("payload")
    bad_dest = os.path.join(TEST_FOLDER, "no_such_subdir", "dst.txt")
    with pytest.raises((OSError, FileNotFoundError)):
        copyfile(src, bad_dest)


def test_make_directory_propagates_failure():
    """
    `make_directory` must raise when the underlying OS call fails. We force
    failure by trying to create a directory whose parent is a regular file.
    """
    blocker = os.path.join(TEST_FOLDER, "blocker_file")
    with open(blocker, "w") as f:
        f.write("not a directory")
    nested = os.path.join(blocker, "child")
    with pytest.raises((OSError, FileExistsError, NotADirectoryError)):
        make_directory(nested)


def test_remove_directory_missing_is_noop():
    """
    Removing a non-existent directory must NOT raise; it is logged and
    treated as success.
    """
    missing = os.path.join(TEST_FOLDER, "totally_absent_dir_xyz")
    remove_directory(missing)  # must not raise


def test_remove_files_swallows_per_item():
    """
    `remove_files` is best-effort: a missing entry in the middle of the list
    must not stop later removals, and no exception is raised.
    """
    keeper = os.path.join(TEST_FOLDER, "rfb_keeper.txt")
    with open(keeper, "w") as f:
        f.write("payload")
    # Order matters: missing entry between two real ones
    real_a = os.path.join(TEST_FOLDER, "rfb_a.txt")
    real_b = os.path.join(TEST_FOLDER, "rfb_b.txt")
    for p in (real_a, real_b):
        with open(p, "w") as f:
            f.write("x")
    missing = os.path.join(TEST_FOLDER, "rfb_missing.txt")

    remove_files([real_a, missing, real_b])  # must not raise
    assert not file_exists(real_a)
    assert not file_exists(real_b)


def test_get_config_missing_raises():
    """
    `get_config` must raise when none of the sources provide the requested
    keys (previously fell off the end and returned None).
    """
    with pytest.raises(RuntimeError):
        get_config(
            keys=["never_set_anywhere_xyz_123"],
            config_type="bogus",
            path=None,
            env_files=[],
        )


def test_get_config_env_files():
    """
    Test the `get_config` function with .env files.

    - Creates a `.env` file with sample data.
    - Verifies the function correctly loads configuration values.
    """
    env_path = os.path.join(TEST_FOLDER, ".env")  # Define .env file path
    # Write test configuration to the .env file
    with open(env_path, "w") as f:
        f.write("API_KEY=env_file_api_key\nDB_URL=env_file_postgres_url\n")
    keys = ["api_key", "db_url"]  # Define keys to retrieve
    config = get_config(keys=keys, config_type="API", env_files=[env_path])  # Load config
    assert config["api_key"] == "env_file_api_key"  # Verify key
    assert config["db_url"] == "env_file_postgres_url"  # Verify key


def test_hashfolder_content():
    """
    Test the `hashfolder` function with content hashing.

    - Creates a folder with files and computes its hash.
    - Modifies a file and verifies the hash changes.
    """
    test_folder = os.path.join(TEST_FOLDER, "hashfolder_test")
    os.makedirs(test_folder)  # Create the folder
    # Create test files
    file1 = os.path.join(test_folder, "file1.txt")
    file2 = os.path.join(test_folder, "file2.txt")
    with open(file1, "w") as f:
        f.write("File 1 content")
    with open(file2, "w") as f:
        f.write("File 2 content")
    initial_hash = hashfolder(test_folder, hash_content=True)  # Compute initial hash
    with open(file1, "w") as f:
        f.write("Modified File 1 content")  # Modify a file
    modified_hash = hashfolder(test_folder, hash_content=True)  # Recompute hash
    assert initial_hash != modified_hash  # Verify the hash changes


def test_folder_description():
    """
    `folder_description` lists non-hidden files with sizes and emits
    `index.html` + `description.json` next to the folder when requested.
    """
    test_dir = os.path.join(TEST_FOLDER, "folder_description_test")
    os.makedirs(test_dir)
    nested = os.path.join(test_dir, "sub")
    os.makedirs(nested)

    with open(os.path.join(test_dir, "a.txt"), "w") as f:
        f.write("aaa")  # 3 bytes
    with open(os.path.join(nested, "b.txt"), "w") as f:
        f.write("bbbb")  # 4 bytes
    # Hidden file must be ignored
    with open(os.path.join(test_dir, ".hidden"), "w") as f:
        f.write("ignored")

    description = folder_description(
        test_dir,
        recursive=True,
        index_html=True,
        with_size=True,
        description_json=True,
    )

    assert description == {"a.txt": 3, os.path.join("sub", "b.txt"): 4}
    assert file_exists(os.path.join(test_dir, "index.html"), check_empty=True)

    desc_json = os.path.join(test_dir, "description.json")
    assert file_exists(desc_json, check_empty=True)
    with open(desc_json) as f:
        assert json.load(f) == description

    # Non-recursive variant on a fresh folder excludes nested entries
    # and emits no companion files.
    flat_dir = os.path.join(TEST_FOLDER, "folder_description_flat")
    os.makedirs(flat_dir)
    os.makedirs(os.path.join(flat_dir, "sub"))
    with open(os.path.join(flat_dir, "a.txt"), "w") as f:
        f.write("aaa")
    with open(os.path.join(flat_dir, "sub", "b.txt"), "w") as f:
        f.write("bbbb")

    flat = folder_description(flat_dir, recursive=False, index_html=False, description_json=False)
    assert flat == {"a.txt": 3}
    assert not file_exists(os.path.join(flat_dir, "index.html"))
    assert not file_exists(os.path.join(flat_dir, "description.json"))


def test_temporary_folder():
    """
    Test the `temporary_folder` function.

    - Creates a temporary folder and verifies its existence.
    - Creates a file in the folder and verifies it exists.
    - Verifies the folder is deleted after the context manager exits.
    """
    with temporary_folder() as temp_folder:
        assert dir_exists(temp_folder)  # Verify the temporary folder exists
        filename = join(temp_folder, "test.txt")
        with open(filename, "w") as f:
            f.write("Temporary file content")
        assert file_exists(filename)
    time.sleep(0.1)  # Wait for the context manager to exit
    assert not dir_exists(temp_folder)  # Verify the temporary folder is deleted


def test_temporary_filename():
    """
    Test the `temporary_filename` function.

    - Creates a temporary file and verifies its existence.
    - Verifies the file is deleted after the context manager exits.
    """
    with temporary_filename() as temp_file:
        assert file_exists(temp_file)  # Verify the temporary file exists
    time.sleep(0.1)  # Wait for the context manager to exit
    assert not file_exists(temp_file)  # Verify the temporary file is deleted


def test_temporary_remote_file_creates_and_cleans_up():
    """
    `temporary_remote_file` should upload a new temp file, expose its remote
    handle, and delete the remote artifact when the block exits.
    """
    storage = {}

    def upload(local_path):
        with open(local_path, "rb") as f:
            storage[local_path] = f.read()
        return local_path  # use the local path as the "remote" id

    def delete(remote_path):
        storage.pop(remote_path, None)

    def check(remote_path):
        return remote_path in storage

    with temporary_remote_file(
        upload,
        delete,
        prefix="trf",
        suffix=".bin",
        checkfile_function=check,
        initial_content=b"hello",
    ) as remote:
        assert remote in storage
        assert storage[remote] == b"hello"

    assert remote not in storage  # cleanup ran


def test_temporary_remote_file_from_local():
    """
    When `from_local_file` is provided, the user-supplied local file must
    survive the block — only the remote artifact gets deleted.
    """
    local_path = join(TEST_FOLDER, "trf_local.txt")
    with open(local_path, "wb") as f:
        f.write(b"local content")

    storage = {}

    def upload(p):
        with open(p, "rb") as f:
            storage[p] = f.read()
        return p

    def delete(r):
        storage.pop(r, None)

    with temporary_remote_file(upload, delete, from_local_file=local_path) as remote:
        assert storage[remote] == b"local content"

    assert remote not in storage
    assert file_exists(local_path)  # local file must NOT be removed


def test_temporary_remote_file_check_failure_raises():
    """
    A failing `checkfile_function` should raise RuntimeError and still
    invoke `delete_function` for cleanup.
    """
    deleted = []

    def upload(p):
        return "remote://" + os.path.basename(p)

    def delete(r):
        deleted.append(r)

    def always_false(_):
        return False

    with (
        pytest.raises(RuntimeError),
        temporary_remote_file(
            upload,
            delete,
            prefix="trf",
            suffix=".bin",
            checkfile_function=always_false,
            initial_content=b"x",
        ) as _remote,
    ):
        pass

    assert len(deleted) == 1  # cleanup still ran


# ---------------------------------------------------------------------------
# profile_utils — wall_timer / cpu_timer / gpu_timer / tic / toc
# ---------------------------------------------------------------------------


def test_wall_timer_measures_sleep():
    with wall_timer() as t:
        time.sleep(0.05)
    assert t["seconds"] >= 0.04  # tolerate timer jitter
    assert abs(t["milliseconds"] - t["seconds"] * 1000) < 1e-6


def test_cpu_timer_skips_sleep():
    """`cpu_timer` must NOT count time spent sleeping (no CPU work)."""
    with cpu_timer() as t:
        time.sleep(0.1)
    assert t["seconds"] < 0.05  # sleeping consumes ~no CPU


def test_cpu_timer_counts_busy_work():
    with cpu_timer() as t:
        s = sum(i * i for i in range(500_000))
    assert s > 0
    assert t["seconds"] > 0


def test_tic_toc_basic():
    tic()
    time.sleep(0.02)
    elapsed = toc()
    assert elapsed >= 0.015


def test_tic_toc_handle_for_nested_timings():
    """Explicit handle survives a subsequent tic()."""
    outer = tic()
    time.sleep(0.02)
    inner = tic()
    time.sleep(0.02)
    inner_elapsed = toc(inner)
    outer_elapsed = toc(outer)
    assert outer_elapsed > inner_elapsed
    # Implicit toc() reads the most recent tic() (inner).
    assert abs(toc() - inner_elapsed) < 0.02


def test_toc_without_tic_raises():
    # Reset the implicit global by forcing it None via a fresh tic+toc cycle,
    # then nuke it. We re-import the module to reset clean module state.
    import os_helper.profile_utils as pu

    pu._LAST_TIC = None
    with pytest.raises(RuntimeError, match="toc"):
        toc()


def test_gpu_timer_raises_when_no_gpu():
    """Without torch, or without CUDA/MPS, gpu_timer must raise RuntimeError.

    We can't always assert the absence of GPU, so we just check that the
    raise path is reachable: ask for a backend that almost certainly isn't
    available on a CI runner (e.g. ``cuda`` on a Mac), and verify the
    error type is RuntimeError (not, say, AttributeError).
    """
    try:
        import torch  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError), gpu_timer():
            pass
        return

    import torch

    if not torch.cuda.is_available():
        with pytest.raises(RuntimeError), gpu_timer(backend="cuda"):
            pass


def test_gpu_timer_rejects_unknown_backend():
    try:
        import torch  # noqa: F401
    except ImportError:
        pytest.skip("torch not installed — bad-backend test runs only when torch is importable")
    # Combined context: assert the ValueError is raised as the bad backend is
    # resolved inside the timer's setup.
    with pytest.raises(ValueError, match="Unknown gpu_timer backend"), gpu_timer(backend="bogus"):
        pass


def test_adaptive_chunk_size_scales_and_clamps() -> None:
    """`download_file`'s block-size picker targets ~512 chunks, clamped [64 KiB, 4 MiB].

    The block size is a local buffering knob (not a wire-packet size); sizing it
    by the payload keeps progress-bar redraws and per-iteration overhead stable
    from a tiny config to a multi-GB model. This pins the four regimes: a mid
    size scales linearly, a huge size hits the ceiling, a tiny size hits the
    floor, and an unknown size (no Content-Length) falls back to the default.
    """
    from os_helper.misc_utils import _adaptive_chunk_size

    lo, hi, default = 64 * 1024, 4 * 1024 * 1024, 1 << 20
    # ~750 MB → 786432000 // 512 = 1_536_000 B, inside the clamp window.
    assert _adaptive_chunk_size(750 * 1024 * 1024) == 1_536_000
    # 5 GB → would be ~10 MiB, clamped down to the 4 MiB ceiling.
    assert _adaptive_chunk_size(5 * 1024**3) == hi
    # 10 KB → would be tiny, clamped up to the 64 KiB floor so it still streams.
    assert _adaptive_chunk_size(10 * 1024) == lo
    # Unknown / zero size (server sent no Content-Length) → fixed 1 MiB fallback.
    assert _adaptive_chunk_size(None) == default
    assert _adaptive_chunk_size(0) == default


def test_progress_bar_config_and_auto_disable(monkeypatch) -> None:
    """`progress_bar` is byte-scaled, honours an explicit disable, and auto-quiets off-TTY.

    This is the shared transfer bar every helper reuses (HTTP download, S3, SFTP),
    so its two contracts matter: byte units with a known total, and — crucially —
    auto-suppression when stderr is not an interactive terminal so CI logs are not
    flooded with carriage returns.
    """
    from os_helper import progress_bar

    # Explicit disable is honoured verbatim; the known total is wired through.
    bar = progress_bar(total=2048, desc="x", disable=True)
    assert bar.total == 2048 and bar.disable is True
    bar.close()

    # disable=None + a non-TTY stderr → auto-disabled (no control-char spam in CI).
    monkeypatch.setattr("sys.stderr.isatty", lambda: False)
    off = progress_bar(total=10, disable=None)
    assert off.disable is True
    off.close()


def test_init_logging_named_live_stream(monkeypatch) -> None:
    """`init_logging(name=..., live_stream=True)` is CLI-friendly: named, idempotent,
    live-stderr, and propagating.

    This is the mode a CLI needs to route its diagnostics through os_helper without
    losing pytest's ``capsys``/``caplog`` capture: (1) it configures a *named*
    logger with a bare format, (2) a repeat call does not stack a duplicate
    handler, (3) the handler re-resolves ``sys.stderr`` on each emit so a stream
    swapped *after* configuration still receives records, and (4) ``propagate=True``
    keeps records visible to a root/``caplog`` handler.
    """
    import io
    import logging
    import sys

    from os_helper import init_logging

    lg = init_logging(
        name="oshtest", level=logging.ERROR, stdout=False, log_format="%(message)s",
        use_colors=False, capture_warnings=False, live_stream=True, propagate=True,
    )
    try:
        assert lg.name == "oshtest" and lg.level == logging.ERROR and lg.propagate is True

        # Idempotency: a second call must not add a second owned console handler.
        init_logging(name="oshtest", level=logging.ERROR, stdout=False,
                     log_format="%(message)s", use_colors=False, live_stream=True,
                     propagate=True)
        owned = [h for h in logging.getLogger("oshtest").handlers
                 if getattr(h, "_osh_owned", False)]
        assert len(owned) == 1

        # Live-stderr: swap sys.stderr AFTER config; the record lands in the new one,
        # bare (no level/timestamp prefix), and the sub-ERROR line is dropped.
        child = logging.getLogger("oshtest.sub")
        buf = io.StringIO()
        old = sys.stderr
        sys.stderr = buf
        try:
            child.warning("dropped below ERROR")
            child.error("bare message")
        finally:
            sys.stderr = old
        assert buf.getvalue() == "bare message\n"

        # propagate=True → a root handler still observes the record.
        seen: list[str] = []
        probe = logging.Handler()
        probe.emit = lambda r: seen.append(r.getMessage())
        logging.getLogger().addHandler(probe)
        try:
            child.error("also at root")
        finally:
            logging.getLogger().removeHandler(probe)
        assert "also at root" in seen
    finally:
        # Tear down so the named logger doesn't leak into other tests.
        for h in logging.getLogger("oshtest").handlers[:]:
            logging.getLogger("oshtest").removeHandler(h)

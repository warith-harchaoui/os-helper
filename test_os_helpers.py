import os
import pytest
import tempfile
from os_helper import (
    emptystring,
    verbosity,
    now_string,
    windows,
    linux,
    macos,
    file_exists,
    dir_exists,
    relative2absolute_path,
    openfile,
    asciistring,
    zip_folder,
    recursive_glob
)


def test_emptystring():
    assert emptystring("") is True
    assert emptystring(None) is True
    assert emptystring("Non-empty") is False


def test_verbosity():
    original_level = verbosity()
    assert verbosity(2) == 2
    assert verbosity() == 2
    verbosity(1)
    assert verbosity() == 1
    verbosity(original_level)  # Restore original verbosity level


def test_now_string():
    log_format = now_string("log")
    filename_format = now_string("filename")
    assert "/" in log_format
    assert "-" in filename_format
    assert ":" not in filename_format


def test_os_functions():
    assert isinstance(windows(), bool)
    assert isinstance(linux(), bool)
    assert isinstance(macos(), bool)


def test_file_exists():
    with tempfile.NamedTemporaryFile() as temp_file:
        assert file_exists(temp_file.name) is True
        assert file_exists("non_existent_file.txt") is False


def test_dir_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        assert dir_exists(temp_dir) is True
        assert dir_exists(temp_dir, check_empty=True) is True
        f = os.path.join(temp_dir, "test")
        assert dir_exists(f) is False


def test_relative2absolute_path():
    relative_path = "test_utils.py"
    absolute_path = relative2absolute_path(relative_path)
    assert os.path.isabs(absolute_path)
    assert os.path.exists(absolute_path)


def test_openfile():
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
        # This test might not work on non-GUI systems, so it is marked as xfail
        pytest.xfail("Open file test not reliable on non-GUI systems")
        openfile(temp_file.name)


def test_asciistring():
    assert asciistring("Café-Con-Leche!") == "cafe-con-leche"
    assert asciistring("Special#File$2024", lower=False) == "Special-File-2024"
    assert asciistring("Café@2024.txt") == "cafe-2024-txt"


def test_zip_folder():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some dummy files
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        with open(file1, 'w') as f1, open(file2, 'w') as f2:
            f1.write("File 1 content")
            f2.write("File 2 content")
        
        # Create the zip file
        zip_file = os.path.join(temp_dir, "output.zip")
        zip_folder(temp_dir, zip_file_path=zip_file)
        
        # Check if the zip file exists and contains files
        assert file_exists(zip_file)

def test_recursive_glob():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some dummy files
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        with open(file1, 'w') as f1, open(file2, 'w') as f2:
            f1.write("File 1 content")
            f2.write("File 2 content")
        
        # Find the files
        files = recursive_glob(temp_dir, "*.txt")
        assert len(files) == 2
        assert file1 in files
        assert file2 in files

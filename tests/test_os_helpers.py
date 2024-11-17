import os
import json
import time
import yaml
import pytest
from os_helper import (
    emptystring,
    verbosity,
    now_string,
    file_exists,
    dir_exists,
    relative2absolute_path,
    temporary_folder,
    temporary_filename,
    asciistring,
    zip_folder,
    recursive_glob,
    os_path_constructor,
    get_config,
    hashfolder,
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


def test_emptystring():
    """
    Test the `emptystring` function.

    - Verifies it correctly identifies empty strings and None as empty.
    - Verifies it returns False for non-empty strings.
    """
    assert emptystring("") is True  # An empty string should return True
    assert emptystring(None) is True  # None should return True
    assert emptystring("Non-empty") is False  # A non-empty string should return False


def test_verbosity():
    """
    Test the `verbosity` function.

    - Verifies it can set and retrieve verbosity levels.
    - Restores the original verbosity level after testing.
    """
    original_level = verbosity()  # Save the current verbosity level
    assert verbosity(2) == 2  # Set verbosity to 2 and verify
    assert verbosity() == 2  # Retrieve verbosity and verify
    verbosity(1)  # Change verbosity to 1
    assert verbosity() == 1  # Verify the change
    verbosity(original_level)  # Restore the original verbosity level


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
    sub_dir = os_path_constructor([test_dir, "sub_folder"])  # Create a non-existent subdirectory path
    assert dir_exists(sub_dir) is False  # Non-existent directory should return False


def test_relative2absolute_path():
    """
    Test the `relative2absolute_path` function.

    - Converts a relative path to an absolute path and verifies correctness.
    - Ensures relative paths remain unaffected.
    """
    relative_path = os.path.relpath(TEST_FOLDER)  # Get a relative path for testing
    absolute_path = relative2absolute_path(relative_path)  # Convert to absolute path
    assert os.path.isabs(absolute_path), f"Path is not absolute: {absolute_path}"  # Verify the result is absolute
    assert not os.path.isabs(relative_path), f"Path is not relative: {relative_path}"  # Ensure the input is relative


def test_asciistring():
    """
    Test the `asciistring` function.

    - Verifies it converts non-ASCII characters to ASCII equivalents.
    - Verifies it replaces special characters with the replacement character.
    """
    assert asciistring("Café-Con-Leche!") == "cafe-con-leche"  # Replace accented and special characters
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
    file1 = os_path_constructor([test_dir, "file1.txt"])
    file2 = os_path_constructor([test_dir, "file2.txt"])
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
    file1 = os_path_constructor([test_dir, "file1.txt"])
    file2 = os_path_constructor([test_dir, "file2.txt"])
    with open(file1, "w") as f1, open(file2, "w") as f2:
        f1.write("File 1 content")
        f2.write("File 2 content")
    files = recursive_glob(test_dir, "*.txt")  # Search for files matching pattern
    assert len(files) == 2  # Verify two files are found
    assert file1 in files  # Verify specific file is found
    assert file2 in files  # Verify specific file is found


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

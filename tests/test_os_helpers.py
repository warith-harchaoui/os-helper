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

# Define a test folder to work within
TEST_FOLDER = os.path.join(os.getcwd(), "os_helper_test_folder")
os.makedirs(TEST_FOLDER, exist_ok=True)


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Setup and teardown for tests."""
    yield
    # Teardown: Clean up test folder
    for root, dirs, files in os.walk(TEST_FOLDER, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir(TEST_FOLDER)


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


def test_file_exists():
    with temporary_filename(prefix="tempfile", mode="wt") as temp_file:
        assert file_exists(temp_file) is True
        assert file_exists("non_existent_file.txt") is False


def test_dir_exists():
    with temporary_folder(prefix="tempdir_dir_exists") as temp_dir:
        assert dir_exists(temp_dir) is True
        assert dir_exists(temp_dir, check_empty=True) is False
        sub_dir = os_path_constructor([temp_dir, "non_existent_dir"])
        assert dir_exists(sub_dir) is False


def test_relative2absolute_path():
    relative_path = "test_utils.py"
    absolute_path = relative2absolute_path(relative_path)
    assert os.path.isabs(absolute_path), f"Path is not absolute: {absolute_path}"
    assert not os.path.isabs(relative_path), f"Path is not relative: {relative_path}"


def test_asciistring():
    assert asciistring("Café-Con-Leche!") == "cafe-con-leche"
    assert asciistring("Special#File$2024", lower=False) == "Special-File-2024"
    assert asciistring("Café@2024.txt") == "cafe-2024-txt"


def test_zip_folder():
    with temporary_folder(prefix="tempdir") as temp_dir:
        # Create some dummy files
        file1 = os_path_constructor([temp_dir, "file1.txt"])
        file2 = os_path_constructor([temp_dir, "file2.txt"])
        with open(file1, 'wt') as f1, open(file2, 'wt') as f2:
            f1.write("File 1 content")
            f2.write("File 2 content")
        
        # Create the zip file
        zip_file = os.path.join(temp_dir, "output.zip")
        zip_folder(temp_dir, zip_file_path=zip_file)
        
        # Check if the zip file exists and contains files
        assert file_exists(zip_file)


def test_recursive_glob():
    with temporary_folder(prefix="tempdir") as temp_dir:
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


def test_get_config_env_variables():
    """
    Test get_config by simulating environment variables.
    """
    # Set up environment variables
    os.environ["API_KEY"] = "env_api_key"
    os.environ["DB_URL"] = "env_postgres_url"

    # Define keys to retrieve
    keys = ["api_key", "db_url"]

    # Call get_config and assert values
    config = get_config(keys=keys, config_type="API")
    assert config["api_key"] == "env_api_key"
    assert config["db_url"] == "env_postgres_url"


def test_get_config_json_file():
    """
    Test get_config with a valid JSON file.
    """
    # Create a temporary JSON configuration file
    test_json_path = os.path.join(TEST_FOLDER, "config.json")
    test_config = {"api_key": "json_api_key", "db_url": "json_postgres_url"}
    with open(test_json_path, "w") as f:
        json.dump(test_config, f)

    # Define keys to retrieve
    keys = ["api_key", "db_url"]

    # Call get_config and assert values
    config = get_config(keys=keys, config_type="API", path=test_json_path)
    assert config["api_key"] == "json_api_key"
    assert config["db_url"] == "json_postgres_url"


def test_get_config_yaml_file():
    """
    Test get_config with a valid YAML file.
    """
    # Create a temporary YAML configuration file
    test_yaml_path = os.path.join(TEST_FOLDER, "config.yaml")
    test_config = {"api_key": "yaml_api_key", "db_url": "yaml_postgres_url"}
    with open(test_yaml_path, "w") as f:
        yaml.dump(test_config, f)

    # Define keys to retrieve
    keys = ["api_key", "db_url"]

    # Call get_config and assert values
    config = get_config(keys=keys, config_type="API", path=test_yaml_path)
    assert config["api_key"] == "yaml_api_key"
    assert config["db_url"] == "yaml_postgres_url"


def test_hashfolder_content():
    """
    Test hashfolder by verifying its hash changes with folder content.
    """
    # Create a temporary folder with some files
    test_folder = os.path.join(TEST_FOLDER, "hashfolder_test")
    os.makedirs(test_folder, exist_ok=True)
    file1 = os.path.join(test_folder, "file1.txt")
    file2 = os.path.join(test_folder, "file2.txt")
    with open(file1, "w") as f:
        f.write("File 1 content")
    with open(file2, "w") as f:
        f.write("File 2 content")

    # Compute initial hash
    initial_hash = hashfolder(test_folder, hash_content=True)

    # Modify a file and recompute hash
    with open(file1, "w") as f:
        f.write("Modified File 1 content")
    modified_hash = hashfolder(test_folder, hash_content=True)

    assert initial_hash != modified_hash, "Folder hash should change when content is modified"


def test_hashfolder_path_only():
    """
    Test hashfolder with only folder path hashing.
    """
    test_folder = os.path.join(TEST_FOLDER, "hashfolder_path_test")
    os.makedirs(test_folder, exist_ok=True)

    # Compute hash based only on folder path
    path_hash = hashfolder(test_folder, hash_content=False, hash_path=True)

    # Create files in the folder and ensure hash remains the same
    file1 = os.path.join(test_folder, "file1.txt")
    with open(file1, "w") as f:
        f.write("File 1 content")
    unchanged_hash = hashfolder(test_folder, hash_content=False, hash_path=True)

    assert path_hash == unchanged_hash, "Path-only hash should not change when folder content changes"


def test_hashfolder_with_date():
    """
    Test hashfolder with the date included in the hash.
    """
    test_folder = os.path.join(TEST_FOLDER, "hashfolder_date_test")
    os.makedirs(test_folder, exist_ok=True)

    # Compute hash with date
    date_hash1 = hashfolder(test_folder, hash_content=False, date=True)
    time.sleep(1)
    date_hash2 = hashfolder(test_folder, hash_content=False, date=True)

    # Ensure the hash changes because the date is included
    assert date_hash1 != date_hash2, "Hash should change when date is included"

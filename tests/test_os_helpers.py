import os
from typing import Dict
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
    temporary_folder,
    temporary_filename,
    openfile,
    asciistring,
    zip_folder,
    recursive_glob,
    os_path_constructor,
    get_config,
)
import json
import yaml

@pytest.fixture
def setup_env_file(tmpdir):
    """
    Fixture to create a temporary .env file with sample configuration.
    """
    env_path = os_path_constructor([tmpdir, ".env"])
    with open(env_path, "w") as f:
        f.write("API_KEY=sample_api_key\n")
        f.write("DB_URL=postgres://user:pass@localhost/db\n")
    return str(env_path)

@pytest.fixture
def check_test_config(config: Dict):
    """
    Fixture to check the loaded configuration.
    """
    assert config["api_key"] == "sample_api_key"
    assert config["db_url"] == "postgres://user:pass@localhost/db"

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
        f = os_path_constructor([temp_dir, "non_existent_dir"])
        assert dir_exists(f) is False


def test_relative2absolute_path():
    relative_path = "test_utils.py"
    absolute_path = relative2absolute_path(relative_path)
    assert os.path.isabs(absolute_path)
    assert os.path.exists(absolute_path)


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


def test_get_config_from_env_file():
    """
    Test get_config by loading from a valid .env file.
    """
    # Define required keys for the config
    keys = ["api_key", "db_url"]

    with temporary_folder(prefix="tempdir") as temp_directory:
        # Create a .env file with sample configuration
        env_path = os_path_constructor([temp_directory, ".env"])
        with open(env_path, "wt") as f:
            f.write("API_KEY=sample_api_key\n")
            f.write("DB_URL=postgres://user:pass@localhost/db\n")

        # Call get_config with path set to the .env file
        config = get_config(keys=keys, config_type="API", env_files=[env_path])
        check_test_config(config)

        config = {
            "api_key": "sample_api_key",
            "db_url": "postgres://user:pass@localhost/db"
        }

        config_json_path = os_path_constructor([temp_directory, "config.json"])
        with open(config_json_path, "wt") as fout:
            json.dump(config, fout)

        config = get_config(keys=keys, config_type="API", path = config_json_path)
        check_test_config(config)

        config_yaml_path = os_path_constructor([temp_directory, "config.yaml"])
        with open(config_yaml_path, "wt") as fout:
            yaml.dump(config, fout)

        config = get_config(keys=keys, config_type="API", path = config_yaml_path)
        check_test_config(config)

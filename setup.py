# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['os_helper']

package_data = \
{'': ['*']}

install_requires = \
['numpy>=2.1.2,<3.0.0',
 'pandas>=2.2.3,<3.0.0',
 'python-dotenv>=1.0.1,<2.0.0',
 'pyyaml>=6.0.2,<7.0.0',
 'requests>=2.32.3,<3.0.0',
 'validators>=0.34.0,<0.35.0']

setup_kwargs = {
    'name': 'os-helper',
    'version': '0.1.0',
    'description': 'This module provides a collection of utility functions aimed at simplifying various common programming tasks, including file handling, system operations, string manipulation, folder management, and more. The functions are optimized for cross-platform compatibility and robust error handling.',
    'long_description': '# OS Helper\n\n`OS Helper` belongs to a collection of libraries called `AI Helpers` developped for building Artificial Intelligence\n\n[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)\n\n[![logo](logo.png)](https://harchaoui.org/warith/ai-helpers)\n\n\nOS Helper is a Python library that provides utility functions for working with different operating systems.  \n\nIt offers a set of tools to simplify common system operations, file handling, and OS-specific tasks.\n\n# Features\n\n- Operating system detection (Windows, Linux, macOS, Unix)\n- File system operations (create, delete, move, copy)\n- System information retrieval (CPU, memory, disk usage)\n- Cross-platform path handling\n- File hashing and string hashing utilities\n- Process management and execution\n\n# Installation\n\n## Install Package\n\nWe can recommand python environments. Check this link if you don\'t know how\n\n[🥸 Tech tips](https://harchaoui.org/warith/4ml/#install)\n\n\n```bash\npip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/os-helper.git@main\n```\n\n## Usage\n\nBelow are examples demonstrating how to use various features of the `os_helper` library. Make sure to import the library as `osh` before starting.\n\n```python\nimport os_helper as osh\n```\n\n1. Set Verbosity and Check Operating System\n\n```python\n# Set verbosity level to display debugging messages\nosh.verbosity(3)\n\n# Check if the system is Unix-based (Linux or macOS)\nif osh.unix():\n    osh.info("You are running on a Unix-based system.")\nelse:\n    osh.info("You are not running on a Unix-based system.")\n```\n\n2. Timestamp and File Existence Check\n```python\n# Generate a formatted timestamp for logging\ntimestamp = osh.now_string("log")\nosh.info(f"Current timestamp (log format): {timestamp}")\n\n# Check if a file exists and is not empty\ntest_file = "example.txt"\nif osh.file_exists(test_file, check_empty=True):\n    osh.info(f"File {test_file} exists and is not empty.")\nelse:\n    osh.error(f"File {test_file} does not exist or is empty.")\n```\n\n3. Directory Creation and File Search\n```python\n# Create a directory\ntest_dir = "test_directory"\nosh.make_directory(test_dir)\nosh.info(f"Directory {test_dir} created.")\n\n# Perform recursive search for \'.txt\' files in the directory\nmatching_files = osh.recursive_glob(test_dir, "*.txt")\nosh.info(f"Matching files: {matching_files}")\n```\n\n4. Copy and Remove Files\n```python\n# Copy a file from source to destination\nsource_file = "source.txt"\ndestination_file = "backup_source.txt"\nosh.copyfile(source_file, destination_file)\nosh.info(f"File {source_file} copied to {destination_file}")\n\n# Remove the copied file\nosh.remove_files([destination_file], verbose=True)\n```\n\n\n\n5. Decompose a Path and Temporary File Creation\n```python\n# Decompose a file path into folder, basename, and extension\nfolder, basename, ext = osh.folder_name_ext("/path/to/myfile.tar.gz")\nosh.info(f"Folder: {folder}, Basename: {basename}, Extension: {ext}")\n\n# Create and write to a temporary file\nwith osh.temporary_filename(suffix=".log") as temp_log:\n    osh.info(f"Temporary file created at: {temp_log}")\n    with osh.open(temp_log, "w") as log_file:\n        log_file.write("This is a temporary log entry.")\n\n```\n\n\n\n\n6. Running System Commands\n```python\n# Execute a system command and capture its output\ncmd_output = osh.system("echo \'Hello, World!\'")\nosh.info(f"Command output: {cmd_output[\'out\']}")\n\n```\n\n\n7. Hashing Files and Strings\n```python\n# Hash the contents of a file\nfile_to_hash = "testfile.txt"\nif osh.file_exists(file_to_hash):\n    file_hash = osh.hashfile(file_to_hash)\n    osh.info(f"Hash of {file_to_hash}: {file_hash}")\n\n# Hash a string with a specific length\nhashed_string = osh.hash_string("MyTestString", size=8)\nosh.info(f"Hashed string: {hashed_string}")\n```\n\n8. ASCII String Conversion and Process ID\n```python\n# Convert a string into a safe ASCII format\nsafe_string = osh.asciistring("Café-Con-Leche!", replacement_char="_")\nosh.info(f"Safe ASCII string: {safe_string}")\n\n# Get the current process ID\npid = osh.getpid()\nosh.info(f"Current Process ID: {pid}")\n```\n\n9. Check URL Validity and Zip Folder\n```python\n# Check if a URL is valid and reachable\nurl = "https://www.example.com"\nif osh.is_working_url(url):\n    osh.info(f"The URL {url} is valid and reachable.")\nelse:\n    osh.error(f"The URL {url} is not reachable.")\n\n# Zip a folder\nfolder_to_zip = "my_folder"\nzip_output = "my_folder_backup.zip"\nosh.zip_folder(folder_to_zip, zip_output)\nosh.info(f"Folder {folder_to_zip} zipped into {zip_output}")\n```\n\n# Authors\n - [Warith Harchaoui](https://harchaoui.org/warith)\n - [Mohamed Chelali](https://mchelali.github.io)\n - [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug)\n\n',
    'author': 'Warith Harchaoui',
    'author_email': 'warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.13,<4.0',
}


setup(**setup_kwargs)


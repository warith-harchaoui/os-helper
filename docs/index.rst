.. OS Helper documentation master file, created by
   sphinx-quickstart on Sun Nov 17 18:36:02 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

OS Helper Documentation
=======================

**OS Helper** is a Python library designed to simplify common programming tasks.  
Part of the **AI Helpers** collection, it includes tools for file handling, system operations, folder management, string manipulation, and more, with robust cross-platform support.

[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)

.. image:: ../assets/logo.png
   :target: https://harchaoui.org/warith/ai-helpers
   :alt: OS Helper Logo
   :align: center

Overview
--------

This module provides a collection of utility functions optimized for:
- **Cross-platform compatibility** (Windows, Linux, macOS, Unix).
- **File handling**: creation, deletion, movement, and validation.
- **System operations**: process management, OS detection, and command execution.
- **String manipulation**: ASCII-safe conversions and hashing utilities.
- **Folder management**: recursive searches, path handling, and zipping utilities.

Authors:
- `Warith Harchaoui <https://harchaoui.org/warith>`_
- `Mohamed Chelali <https://mchelali.github.io>`_
- `Bachir Zerroug <https://www.linkedin.com/in/bachirzerroug>`_

Dependencies:
-------------
The library relies on the following Python packages and standard modules:

- contextlib, glob, hashlib, json, logging, os, pathlib, requests
- shutil, subprocess, tempfile, numpy, yaml, validators, zipfile, dotenv

Installation
------------

To install **OS Helper**, use the following pip command:

.. code-block:: bash

   pip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/os-helper.git@v1.0.0

Usage
-----

Here's how to use **OS Helper** to streamline your tasks:

1. Set verbosity and check the OS type:

   .. code-block:: python

      import os_helper as osh

      osh.verbosity(3)
      if osh.unix():
          osh.info("Running on a Unix-based system.")
      else:
          osh.error("Not running on Unix.")

2. File and directory operations:

   .. code-block:: python

      osh.make_directory("new_folder")
      if osh.file_exists("example.txt"):
          osh.copyfile("example.txt", "new_folder/example_copy.txt")

3. String manipulation and hashing:

   .. code-block:: python

      safe_string = osh.asciistring("Café-Con-Leche!", replacement_char="_")
      file_hash = osh.hashfile("example.txt")

4. Folder management:

   .. code-block:: python

      osh.zip_folder("my_folder", "my_folder_backup.zip")

5. System command execution:

   .. code-block:: python

      cmd_output = osh.system("echo 'Hello, OS Helper!'")
      print(cmd_output["out"])

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api_reference
   modules


Get Started
-----------

Explore the **Usage Guide** or jump straight into the **API Reference** to unlock the full potential of **OS Helper**.

Links
-----

- [GitHub Repository](https://github.com/warith-harchaoui/os-helper)
- [AI Helpers Collection](https://harchaoui.org/warith/ai-helpers)

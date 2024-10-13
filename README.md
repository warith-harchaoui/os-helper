# OS Helper

`OS Helper` belongs to a collection of libraries called `AI Helpers` developped for building Artificial Intelligence

[🕸️ AI Helpers](https://harchaoui.org/warith/ai-helpers)

[![logo](logo.png)](https://harchaoui.org/warith/ai-helpers)


OS Helper is a Python library that provides utility functions for working with different operating systems.  

It offers a set of tools to simplify common system operations, file handling, and OS-specific tasks.

# Features

- Operating system detection (Windows, Linux, macOS, Unix)
- File system operations (create, delete, move, copy)
- System information retrieval (CPU, memory, disk usage)
- Cross-platform path handling
- File hashing and string hashing utilities
- Process management and execution

# Installation

## Install Package

We can recommand python environments. Check this link if you don't know how

[🥸 Tech tips](https://harchaoui.org/warith/4ml/#install)


```bash
pip install --force-reinstall --no-cache-dir git+https://github.com/warith-harchaoui/os-helper.git@main
```

## Usage

Here are an example of how to use OS helper:
```python
import os_helper as osh

# Get number of CPU cores available in your machine
print(osh.get_nb_workers())
```

# Authors
 - [Warith Harchaoui](https://harchaoui.org/warith)
 - [Mohamed Chelali](https://mchelali.github.io)
 - [Bachir Zerroug](https://www.linkedin.com/in/bachirzerroug)


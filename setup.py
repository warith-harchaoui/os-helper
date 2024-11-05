# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['os_helper']

package_data = \
{'': ['*']}

install_requires = \
['numpy>=2.0.0,<2.1.0',
 'pandas>=2.2.3,<3.0.0',
 'python-dotenv>=1.0.1,<2.0.0',
 'pyyaml>=6.0.2,<7.0.0',
 'requests>=2.32.3,<3.0.0',
 'tqdm>=4.66.6,<5.0.0',
 'validators>=0.34.0,<0.35.0']

setup_kwargs = {
    'name': 'os-helper',
    'version': '1.0.0',
    'description': 'This module provides a collection of utility functions aimed at simplifying various common programming tasks, including file handling, system operations, string manipulation, folder management, and more. The functions are optimized for cross-platform compatibility and robust error handling.',
    'long_description': '# OS Helper\n\n`OS Helper` belongs to a collection of libraries called `AI Helpers` developped for building Artificial Intelligence',
    'author': 'Warith Harchaoui',
    'author_email': 'warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.10,<4.0',
}


setup(**setup_kwargs)


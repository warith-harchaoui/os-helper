#!/bin/zsh


# This is an attempt to automate the process of setting up a new Python project using Poetry.
# DO NOT RUN IT LIKE A SCRIPT, copy and paste the commands one by one in your terminal.

# Enable debug and error checking
set -x  # Print each command before executing it
set -e  # Exit the script immediately on any command failure

# Configurations
PROJECT_NAME="os-helper"
PYTHON_VERSION="3.12"
ENV="env4osh"
DEPENDENCIES="setuptools requests python-dotenv numpy pandas pyyaml validators tqdm"
DESCRIPTION="This module provides a collection of utility functions aimed at simplifying various common programming tasks, including file handling, system operations, string manipulation, folder management, and more. The functions are optimized for cross-platform compatibility and robust error handling."
AUTHORS="Warith Harchaoui <warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com>"

conda init
source ~/.zshrc

# Conda environment setup (optional, use only if Conda is required for some reason)
if conda info --envs | grep -q "^$ENV"; then
    echo "Environment $ENV already exists, removing it..."
    conda deactivate
    conda deactivate
    conda remove --name $ENV --all -y
fi


echo "Creating environment $ENV..."
conda create -y -n $ENV python=$PYTHON_VERSION
conda activate $ENV

# Poetry setup
pip install --upgrade poetry poetry2setup

# Remove previous Poetry files if they exist
rm -f pyproject.toml poetry.lock

# Initialize the Poetry project with required details
poetry init --name $PROJECT_NAME --description "$DESCRIPTION" --author "$AUTHORS" --python "^$PYTHON_VERSION" -n

# Convert the dependencies string into an array (compatible with zsh/bash)
DEP_ARRAY=(${=DEPENDENCIES})

# Loop through each dependency and add it with poetry
for dep in "${DEP_ARRAY[@]}"; do
    echo "Adding $dep..."
    poetry add "$dep"
done

# Lock and install dependencies
poetry install

# Generate setup.py and export requirements.txt
poetry2setup > setup.py
poetry export -f requirements.txt --output requirements.txt --without-hashes

# replace git commit hash with @main
sed -i '' 's/@[a-f0-9]\{7,40\}/@main/g' requirements.txt


# Create environment.yml for conda users (optional)
cat <<EOL > environment.yml
name: $ENV
channels:
  - defaults
dependencies:
  - python=$PYTHON_VERSION
  - pip
  - pip:
      - -r file:requirements.txt
EOL

echo "Project setup completed successfully!"

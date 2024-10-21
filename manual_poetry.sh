# This is an attempt to automate the process of setting up a new Python project using Poetry.
# DO NOT RUN IT LIKE A SCRIPT, copy and paste the commands one by one in your terminal.

# Project and Python setup
PROJECT_NAME="os-helper"
PYTHON_VERSION="3.13"
ENV="env4osh"
DEPENDENCIES="requests python-dotenv numpy pandas pyyaml validators"
DESCRIPTION="This module provides a collection of utility functions aimed at simplifying various common programming tasks, including file handling, system operations, string manipulation, folder management, and more. The functions are optimized for cross-platform compatibility and robust error handling."
AUTHORS="Warith Harchaoui <warith.harchaoui@gmail.com>, Mohamed Chelali <mohamed.t.chelali@gmail.com>, Bachir Zerroug <bzerroug@gmail.com>"

conda deactivate 
conda remove --name $ENV --all -y

conda update -y -n base -c defaults conda
conda create -y -n $ENV python=$PYTHON_VERSION
conda activate $ENV
conda install pip -y

yes | pip install poetry
yes | pip install poetry2setup

# Remove previous files if they exist
rm pyproject.toml poetry.lock

# Initialize a new Poetry project (quietly) and automatically create a virtual environment
poetry init --name $PROJECT_NAME --python $PYTHON_VERSION -q

# Update pyproject.toml with description and authors
# Update description in pyproject.toml
sed -i '' 's/^description = ""/description = "'"$DESCRIPTION"'"/' pyproject.toml

# Update authors in pyproject.toml
sed -i '' 's|^authors =.*|authors = \["'"$AUTHORS"'"\]|' pyproject.toml

# Update python version in the pyproject.toml
sed -i '' "s/python = \".*\"/python = \"^$PYTHON_VERSION\"/" pyproject.toml


# Add the required dependencies
# Loop through each dependency and add it with poetry
# Convert the dependencies string into an array using a loop (compatible with zsh)
# Convert the space-separated string into an array in zsh
DEP_ARRAY=(${=DEPENDENCIES})

# Loop through each dependency and add it with poetry
for dep in "${DEP_ARRAY[@]}"; do
    echo "Adding $dep..."
    poetry add $dep
done


# Lock and install dependencies
poetry lock
poetry install

poetry2setup > setup.py
# poetry export -f requirements.txt --output requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes


cat <<EOL > environment.yml
name: $PROJECT_NAME
channels:
  - defaults
dependencies:
  - python=$PYTHON_VERSION
  - pip
  - pip:
      - -r file:requirements.txt
EOL
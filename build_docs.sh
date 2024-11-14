#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print each command before executing it (for debugging)
set -x

echo "Starting build process..."

echo "Installing Rust and Cargo..."
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env

echo "Checking Rust and Cargo versions..."
rustc --version
cargo --version

echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

echo "Checking Poetry version..."
poetry --version

echo "Configuring Poetry to use Python 3.12..."
poetry env use python3.12

echo "Installing project dependencies with Poetry..."
poetry install --no-interaction --no-ansi -vvv

echo "Building documentation with MkDocs..."
poetry run python -m mkdocs build --verbose

echo "Build process completed successfully."

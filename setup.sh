#!/bin/bash
set -e  # Exit on error

echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | POETRY_HOME=/app/.poetry python3 -

# Add poetry to PATH
export PATH="/app/.poetry/bin:$PATH"

echo "Configuring Poetry..."
poetry config virtualenvs.create false
poetry config installer.max-workers 10

echo "Installing dependencies..."
poetry install --no-interaction --no-ansi --no-root --only main

echo "Setup completed successfully!" 

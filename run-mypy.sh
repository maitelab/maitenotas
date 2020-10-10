#! /usr/bin/env bash
echo "Running mypy..."
time find . -type f -path "*.py" -and -not -path "./venv/*" | xargs python -m mypy

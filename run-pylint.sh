#! /usr/bin/env bash
echo "Running pylint..."
time find . -type f -path "*.py" -and -not -path "./venv/*" | xargs python -m pylint

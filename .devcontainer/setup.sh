#!/usr/bin/env bash
arguments=()

pip install uv
uv venv
source .venv/bin/activate
echo "source .venv/bin/activate" >> $HOME/.zshrc

if [ -f requirements.dev.txt ]; then
    arguments+="-r requirements.dev.txt "
fi

if [ -f requirements.txt ]; then
    arguments+="-r requirements.txt"
fi

uv pip install $arguments
pre-commit autoupdate
pre-commit install

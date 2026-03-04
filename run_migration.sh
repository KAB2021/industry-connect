#!/bin/zsh
export PATH="/opt/homebrew/bin:/opt/homebrew/Cellar/postgresql@15/15.17/bin:$PATH"
cd /Users/khalidbahassan/Desktop/project
source .venv/bin/activate
alembic upgrade head

#!/usr/bin/env bash
set -euo pipefail

alembic upgrade head || exit 1

exec "$@"

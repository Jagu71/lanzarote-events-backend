#!/bin/sh
set -eu

python -m scripts.init_db
exec python -m scripts.run_scrapers

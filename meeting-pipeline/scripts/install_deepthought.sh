#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3.11 >/dev/null 2>&1; then
  echo "python3.11 is required"
  exit 1
fi

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
python -m pip install -e '.[ml,dev]'

mkdir -p data/input data/processing data/archive data/output data/cache data/logs

echo "Installation complete."
echo "Next steps:"
echo "  1. export HUGGINGFACE_TOKEN=hf_xxx"
echo "  2. source .venv/bin/activate"
echo "  3. meetpipe doctor"

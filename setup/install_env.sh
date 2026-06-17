#!/usr/bin/env bash
# Create the nanodrone-ai conda env and install gym-pybullet-drones.
#
# gym-pybullet-drones is not on conda-forge and its pybullet pin would make pip
# rebuild pybullet from source (which fails on the newest Xcode clang), so we
# install it with --no-deps after conda has provided every dependency.
#
# Prereq: conda/miniforge (run setup/install_macos.sh first if needed).
set -euo pipefail

if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. Run setup/install_macos.sh first, then re-open your shell."
  exit 1
fi

# Make `conda activate` / `conda run` work inside this non-interactive script.
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Creating conda env from environment.yml ..."
conda env create -f "${REPO_ROOT}/environment.yml"

echo "==> Installing gym-pybullet-drones (--no-deps) ..."
conda run -n nanodrone-ai pip install --no-deps \
  "gym-pybullet-drones @ git+https://github.com/utiasDSL/gym-pybullet-drones.git"

echo "==> Installing the shared 'nanodrone' core (editable) ..."
conda run -n nanodrone-ai pip install -e "${REPO_ROOT}"

echo ""
echo "==> Done. Next:"
echo "    conda activate nanodrone-ai"
echo "    python lessons/01_hover/hover_demo.py"

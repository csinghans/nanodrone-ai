#!/usr/bin/env bash
# Install miniforge (conda for Apple Silicon) if it's not already present.
# This does NOT create the project env — run `conda env create -f environment.yml`
# afterwards. Safe to re-run: it skips installation if conda already exists.
set -euo pipefail

echo "==> nanodrone-ai: macOS setup"

# 1. Sanity check: Apple Silicon
ARCH="$(uname -m)"
if [ "$ARCH" != "arm64" ]; then
  echo "WARNING: detected arch '$ARCH', not arm64 (Apple Silicon)."
  echo "This course targets Apple Silicon Macs. You can continue, but"
  echo "PyTorch MPS (GPU) acceleration will not be available."
fi

# 2. Install miniforge if conda is missing
if command -v conda >/dev/null 2>&1; then
  echo "==> conda already installed: $(conda --version)"
else
  echo "==> conda not found. Installing miniforge..."
  INSTALLER="Miniforge3-MacOSX-arm64.sh"
  URL="https://github.com/conda-forge/miniforge/releases/latest/download/${INSTALLER}"
  TMP="$(mktemp -d)"
  echo "    downloading ${URL}"
  curl -fsSL "$URL" -o "${TMP}/${INSTALLER}"
  bash "${TMP}/${INSTALLER}" -b -p "${HOME}/miniforge3"
  rm -rf "$TMP"
  # Initialize conda for the current shell
  # shellcheck disable=SC1091
  source "${HOME}/miniforge3/etc/profile.d/conda.sh"
  conda init "$(basename "${SHELL}")"
  echo "==> miniforge installed at ${HOME}/miniforge3"
fi

echo ""
echo "==> Done. Next steps:"
echo "    1. Restart your terminal (or: source ~/miniforge3/etc/profile.d/conda.sh)"
echo "    2. conda env create -f environment.yml"
echo "    3. conda activate nanodrone-ai"
echo "    4. python lessons/01_hover/hover_demo.py"

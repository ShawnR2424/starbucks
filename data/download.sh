#!/usr/bin/env bash
# Fetch the Starbucks promotion dataset into data/.
# The data is not redistributed in this repo (no stated license).
set -euo pipefail

DATA_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_REPO="https://github.com/01KAT1/Marketing-Promotion-Campaign-Uplift-Modelling-Starbucks-Dataset"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --depth 1 --quiet "$SRC_REPO" "$TMP/src"
cp "$TMP/src/training.csv" "$TMP/src/Test.csv" "$DATA_DIR/"
echo "Downloaded training.csv and Test.csv to $DATA_DIR"

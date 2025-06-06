#!/bin/bash

# Base directory containing the port folders
BASE_DIR="data_filip/AS57043"

# Iterate through all folders named after ports in the base directory
for PORT_DIR in "$BASE_DIR"/*/; do
  # Construct the path to the clean_versions file
  CLEAN_VERSIONS="${PORT_DIR}clean_versionsAS57043.json"

  # Check if the clean_versions file exists
  if [[ -f "$CLEAN_VERSIONS" ]]; then
    echo "Processing $CLEAN_VERSIONS..."

    # Run the best_eol_parallel.py script
    python3 py_scripts/best_eol_parralel.py "$CLEAN_VERSIONS" "$PORT_DIR"
  else
    echo "Skipping $PORT_DIR: clean_versions file not found."
  fi
done
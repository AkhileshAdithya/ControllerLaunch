#!/bin/bash
# Script to generate checksums for ControllerLaunch release artifacts

set -e

# Define variables
VERSION=${1:-"unversioned"}
BASE_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Function to generate checksums
generate_checksums() {
  local file_pattern=$1
  local header=$2
  
  echo "" >> checksums.txt
  echo "## $header" >> checksums.txt
  
  # Find all files matching the pattern and generate checksums
  find "$BASE_DIR" -name "$file_pattern" -type f | while read file; do
    echo "Generating checksums for $(basename "$file")"
    sha256sum "$file" >> checksums.txt
    md5sum "$file" >> checksums.txt
  done
}

# Create or overwrite checksum file
echo "# ControllerLaunch $VERSION Checksums" > checksums.txt
echo "# Generated on $(date)" >> checksums.txt

# Generate checksums for AppImage
generate_checksums "ControllerLaunch*.AppImage" "AppImage"

# Generate checksums for source archives if they exist
if ls "$BASE_DIR"/ControllerLaunch*-source.tar.gz 1> /dev/null 2>&1; then
  generate_checksums "ControllerLaunch*-source.tar.gz" "Source Archive (tar.gz)"
fi

if ls "$BASE_DIR"/ControllerLaunch*-source.zip 1> /dev/null 2>&1; then
  generate_checksums "ControllerLaunch*-source.zip" "Source Archive (zip)"
fi

# Move checksums file to base directory if it's not already there
if [ "$(dirname "$(readlink -f "checksums.txt")")" != "$BASE_DIR" ]; then
  mv checksums.txt "$BASE_DIR"/checksums.txt
fi

echo "Checksums generated successfully at $BASE_DIR/checksums.txt"

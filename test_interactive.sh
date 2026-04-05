#!/bin/bash
# Test script to demonstrate single-key interactive mode
# Run this in a terminal to see the single-key input in action

echo "Creating a fresh test archive..."
rm -rf test_archive
cp -r test_archive_backup test_archive

echo ""
echo "Running duplicate finder in interactive mode..."
echo "You'll be able to press y, n, or q without pressing Enter!"
echo ""

python3 duplicate_finder.py test_archive --no-check-timestamp --delete-interactive

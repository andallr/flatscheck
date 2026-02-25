#!/usr/bin/env bash
# FlatsCheck — One-command launcher
# Fetches conditions and opens the dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "🎣  FlatsCheck — TX Gulf Coast Conditions"
echo "    Redfish · Speckled Trout"
echo ""

# Run the fetcher
python3 fetch_conditions.py

echo ""
echo "Starting local server on http://localhost:8080 ..."
echo "Press Ctrl+C to stop."
echo ""

# Open in browser (macOS)
if command -v open &>/dev/null; then
  sleep 1 && open "http://localhost:8080/dashboard.html" &
fi

# Start a simple HTTP server so fetch() works from dashboard.html
python3 -m http.server 8080

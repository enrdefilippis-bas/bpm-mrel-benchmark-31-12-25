#!/bin/bash
# Starts the MREL benchmark Dash app at http://127.0.0.1:8050
# Double-click this file to launch. Press Ctrl+C in the Terminal window to stop.

cd "$(dirname "$0")"
source venv/bin/activate
echo ""
echo "================================================================"
echo "  MREL benchmark — open http://127.0.0.1:8050 in your browser"
echo "  (Press Ctrl+C in this window to stop the server)"
echo "================================================================"
echo ""
exec python -m app.app

#!/bin/bash
# One-click script launcher for the Composio Research Dashboard server

echo "=========================================================="
echo "🚀 Starting Composio Feasibility & API Research Server..."
echo "=========================================================="

# Check if GEMINI_API_KEY is configured
if [ -z "$GEMINI_API_KEY" ]; then
  echo "⚠️ Warning: GEMINI_API_KEY is not set in your shell environment."
  echo "  Running custom app research will fail unless you export it first:"
  echo "  export GEMINI_API_KEY='your-key'"
  echo "----------------------------------------------------------"
fi

# Run Flask server using uv
uv run --with flask --with google-generativeai --with duckduckgo-search --with requests server.py

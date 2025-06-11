#!/bin/bash
# Test Runner Shell Script for SwarmDirector
# Simple wrapper around the Python test runner

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 SwarmDirector Test Runner (Shell Wrapper)"
echo "=============================================="
echo "📁 Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the Python test runner with all arguments passed through
echo "▶️  Running Python test runner..."
python scripts/run_tests.py "$@"

echo "✅ Test execution complete!" 
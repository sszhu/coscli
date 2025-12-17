#!/bin/bash
# COS CLI Installation Script (uv)

set -e

echo "════════════════════════════════════════"
echo "  COS CLI - Fast Installation with uv"
echo "════════════════════════════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required"
    exit 1
fi

echo "✓ Python $(python3 --version 2>&1 | awk '{print $2}')"

# Install uv if needed
if ! command -v uv &> /dev/null; then
    echo "⬇️  Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env" 2>/dev/null || true
    
    if ! command -v uv &> /dev/null; then
        echo "⚠️  Please run: source \$HOME/.cargo/env"
        exit 1
    fi
fi

echo "✓ uv $(uv --version)"

# Create venv and install
echo ""
echo "📦 Setting up environment..."
cd "$(dirname "$0")"

uv venv --quiet 2>/dev/null || uv venv
source .venv/bin/activate

echo "📥 Installing COS CLI..."
uv pip install -e . --native-tls --quiet

echo ""
echo "════════════════════════════════════════"
echo "✅ Installation Complete!"
echo "════════════════════════════════════════"
echo ""
echo "🚀 Activate environment:"
echo "   source .venv/bin/activate"
echo ""
echo "⚙️  Configure:"
echo "   cos configure"
echo ""
echo "📖 Documentation: docs/"
echo "════════════════════════════════════════"

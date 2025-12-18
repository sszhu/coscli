#!/bin/bash
# COS CLI Installation Script (uv)

set -e

# Show help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "COS CLI Installation Script"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --current, -c    Install in current environment (skip venv creation)"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./install.sh              # Create new venv and install"
    echo "  ./install.sh --current    # Install in current environment"
    exit 0
fi

# Parse command line arguments
USE_CURRENT_ENV=false
if [[ "$1" == "--current" || "$1" == "-c" ]]; then
    USE_CURRENT_ENV=true
fi

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
    
    # Try with SSL verification first
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then
        echo "⚠️  SSL certificate error detected, retrying with --insecure..."
        curl -LsSfk https://astral.sh/uv/install.sh | sh
    fi
    
    source "$HOME/.cargo/env" 2>/dev/null || true
    
    if ! command -v uv &> /dev/null; then
        echo "⚠️  Please run: source \$HOME/.cargo/env"
        exit 1
    fi
fi

echo "✓ uv $(uv --version)"

# Create venv and install
echo ""
cd "$(dirname "$0")"

if [ "$USE_CURRENT_ENV" = true ]; then
    echo "📦 Installing in current environment..."
    
    # Check if we're in a virtual environment
    if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
        echo "⚠️  Warning: Not in a virtual environment"
        echo "   Consider using a venv or conda environment"
        read -p "   Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Installation cancelled"
            exit 1
        fi
    fi
    
    echo "📥 Installing COS CLI..."
    uv pip install -e . --native-tls --quiet
else
    echo "📦 Setting up environment..."
    uv venv --quiet 2>/dev/null || uv venv
    source .venv/bin/activate
    
    echo "📥 Installing COS CLI..."
    uv pip install -e . --native-tls --quiet
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ Installation Complete!"
echo "════════════════════════════════════════"
echo ""

if [ "$USE_CURRENT_ENV" = false ]; then
    echo "🚀 Activate environment:"
    echo "   source .venv/bin/activate"
    echo ""
fi

echo "⚙️  Configure:"
echo "   cos configure"
echo ""
echo "📖 Documentation: docs/"
echo "════════════════════════════════════════"

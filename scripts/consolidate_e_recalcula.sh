#!/bin/bash
# Consolidates partial PNCP and rebuilds gold+IEAS with complete data

set -e
cd "$(dirname "$0")/.."

echo "🔄 Consolidating PNCP..."
uv run python -c "from farol_ss.transform import silver_pncp; silver_pncp.rodar()"

echo "🔄 Rebuilding gold..."
uv run farol gold

echo "🔄 Recalculating IEAS..."
uv run farol ieas

echo "✓ Complete pipeline with updated PNCP"

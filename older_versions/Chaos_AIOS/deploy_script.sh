#!/bin/bash
# =============================================================================
# Chaos AI-OS Deployment Script
# Automates switching between LOCAL and PRODUCTION modes
# =============================================================================

set -e

MODE=$1

show_help() {
    echo "Usage: ./deploy.sh [local|production|status]"
    echo ""
    echo "Commands:"
    echo "  local       - Switch to local testing mode (no API)"
    echo "  production  - Switch to production mode (Claude API)"
    echo "  status      - Check current deployment mode"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh production"
    echo "  ./deploy.sh local"
}

check_status() {
    if grep -q "^    query_lower = query.lower()" orchestrator.py; then
        echo "✅ Current mode: LOCAL TESTING"
        echo "   - Using heuristic-based density estimation"
        echo "   - Placeholder responses"
        echo "   - No API key required"
    elif grep -q "^    import anthropic" orchestrator.py; then
        echo "✅ Current mode: PRODUCTION"
        echo "   - Using Claude API for density estimation"
        echo "   - Real AI responses"
        echo "   - API key: ${ANTHROPIC_API_KEY:0:10}..."
    else
        echo "⚠️  Cannot determine mode - file may be corrupted"
        exit 1
    fi
}

switch_to_production() {
    echo "🚀 Switching to PRODUCTION mode..."
    
    # Check for API key
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo "❌ Error: ANTHROPIC_API_KEY not set"
        echo "   Run: export ANTHROPIC_API_KEY='your-key-here'"
        exit 1
    fi
    
    # Check if anthropic is installed
    if ! python3 -c "import anthropic" 2>/dev/null; then
        echo "❌ Error: anthropic package not installed"
        echo "   Run: pip install anthropic"
        exit 1
    fi
    
    # Backup current file
    cp orchestrator.py orchestrator.py.backup
    echo "📦 Backed up to orchestrator.py.backup"
    
    # Comment out LOCAL MODE blocks (density estimation)
    sed -i.tmp '86,109s/^    /    # /' orchestrator.py
    
    # Uncomment PRODUCTION MODE blocks (density estimation)
    sed -i.tmp '111,136s/^    # /    /' orchestrator.py
    
    # Comment out LOCAL MODE blocks (response generation)
    sed -i.tmp '62,65s/^    /    # /' orchestrator.py
    
    # Uncomment PRODUCTION MODE blocks (response generation)
    sed -i.tmp '67,128s/^    # /    /' orchestrator.py
    
    rm orchestrator.py.tmp
    
    echo "✅ Successfully switched to PRODUCTION mode"
    echo "   Test it: python orchestrator.py 'Hello world'"
}

switch_to_local() {
    echo "🏠 Switching to LOCAL mode..."
    
    # Backup current file
    cp orchestrator.py orchestrator.py.backup
    echo "📦 Backed up to orchestrator.py.backup"
    
    # Uncomment LOCAL MODE blocks (density estimation)
    sed -i.tmp '86,109s/^    # /    /' orchestrator.py
    
    # Comment out PRODUCTION MODE blocks (density estimation)
    sed -i.tmp '111,136s/^    /    # /' orchestrator.py
    
    # Uncomment LOCAL MODE blocks (response generation)
    sed -i.tmp '62,65s/^    # /    /' orchestrator.py
    
    # Comment out PRODUCTION MODE blocks (response generation)
    sed -i.tmp '67,128s/^    /    # /' orchestrator.py
    
    rm orchestrator.py.tmp
    
    echo "✅ Successfully switched to LOCAL mode"
    echo "   Test it: python orchestrator.py 'Hello world'"
}

case "$MODE" in
    production)
        switch_to_production
        ;;
    local)
        switch_to_local
        ;;
    status)
        check_status
        ;;
    *)
        show_help
        exit 1
        ;;
esac
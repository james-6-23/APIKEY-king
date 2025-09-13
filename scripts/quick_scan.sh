#!/bin/bash
# Quick launch scripts for different scanning modes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_ROOT" || exit 1

# Check if src directory exists
if [ ! -d "src" ]; then
    print_error "src directory not found. Are you in the correct project directory?"
    exit 1
fi

# Function to run scanner
run_scanner() {
    local mode="$1"
    local preset="$2"
    
    print_status "Starting APIKEY-king in $mode mode..."
    
    if [ -n "$preset" ]; then
        print_status "Using preset configuration: $preset"
        python -m src.main --mode "$mode" --config-preset "$preset"
    else
        python -m src.main --mode "$mode"
    fi
}

# Main script
case "$1" in
    "openrouter"|"or")
        run_scanner "openrouter-only" "openrouter-only"
        ;;
    "modelscope"|"ms")
        run_scanner "modelscope-only" "modelscope-only"
        ;;
    "gemini"|"gm")
        run_scanner "gemini-only" "gemini-only"
        ;;
    "all"|"compatible")
        run_scanner "compatible"
        ;;
    "help"|"-h"|"--help")
        echo "APIKEY-king Quick Launch Script"
        echo ""
        echo "Usage: $0 <mode>"
        echo ""
        echo "Available modes:"
        echo "  openrouter, or  - Scan for OpenRouter API keys only"
        echo "  modelscope, ms  - Scan for ModelScope API keys only"
        echo "  gemini, gm      - Scan for Gemini API keys only (with validation)"
        echo "  all, compatible - Scan for all types"
        echo ""
        echo "Examples:"
        echo "  $0 openrouter   # Scan only OpenRouter keys"
        echo "  $0 ms           # Scan only ModelScope keys"
        echo "  $0 all          # Scan all types"
        ;;
    *)
        print_error "Unknown mode: $1"
        print_warning "Run '$0 help' for usage information"
        exit 1
        ;;
esac
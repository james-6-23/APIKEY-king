# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APIKEY-king (🎪 Hajimi King 🏆) is a Python-based tool for discovering API keys from GitHub repositories. It specializes in extracting and optionally validating:

- **Gemini API keys** (AIzaSy format) - with validation support
- **ModelScope API keys** (ms-UUID format) - extraction only
- **OpenRouter API keys** (sk-or-v1 format) - extraction only

## Architecture & Core Components

The project follows a modular architecture with clear separation of concerns:

### Core Modules

- **`app/hajimi_king.py`** - Main application entry point and orchestration logic
- **`common/config.py`** - Configuration management with environment variable support
- **`common/Logger.py`** - Enhanced logging system with colors and progress tracking
- **`utils/github_client.py`** - GitHub API interaction and search functionality
- **`utils/file_manager.py`** - File operations, checkpoint management, and data persistence

### Key Features

1. **Multi-mode Operation**: Supports three extraction modes via `--mode` CLI argument
   - `modelscope-only`: Extract only ModelScope keys
   - `openrouter-only`: Extract only OpenRouter keys  
   - `compatible`: Extract all types with fallback to Gemini validation

2. **Incremental Scanning**: Uses checkpoint system to avoid re-processing files
3. **Proxy Support**: Built-in proxy rotation for API rate limit management
4. **Smart Filtering**: Automatically filters documentation, examples, and test files

### Data Flow

1. Load queries from `data/queries.txt`
2. Search GitHub using configured queries
3. Filter results based on repository age, file paths, and previous scans
4. Extract keys based on configured mode and patterns
5. **NEW**: Validate all three types of keys against their respective APIs:
   - **Gemini** keys via Google AI API
   - **OpenRouter** keys via OpenRouter API
   - **ModelScope** keys via ModelScope Chat API
6. Save results to timestamped files in `data/` directory

## Development Commands

### Local Development

```bash
# Install dependencies
uv pip install -r pyproject.toml

# Create data directory and queries file
mkdir -p data
cp queries.template data/queries.txt

# Run with different modes
python app/hajimi_king.py --mode compatible
python app/hajimi_king.py --mode modelscope-only
python app/hajimi_king.py --mode openrouter-only
```

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

The application uses environment variables loaded from `.env` file (copy from `.env.template`):

### Required Configuration
- `GITHUB_TOKENS`: Comma-separated GitHub API tokens (required)

### Key Optional Settings
- `DATA_PATH`: Data storage directory (default: `./data`)
- `PROXY`: Proxy configuration for rate limit management
- `TARGET_BASE_URLS`: ModelScope API endpoints to detect
- `OPENROUTER_BASE_URLS`: OpenRouter API endpoints to detect
- `QUERIES_FILE`: Search query configuration file
- `DATE_RANGE_DAYS`: Repository age filter in days

## File Structure & Output

### Input Files
- `data/queries.txt`: GitHub search queries (one per line, supports GitHub search syntax)
- `.env`: Environment configuration

### Output Files (timestamped)
- `data/keys/keys_valid_YYYYMMDD.txt`: Valid API keys
- `data/keys/key_429_YYYYMMDD.txt`: Rate-limited keys
- `data/logs/keys_valid_detail_YYYYMMDD.log`: Detailed extraction logs

### State Files
- `data/checkpoint.json`: Scan progress and processed queries
- `data/scanned_shas.txt`: Previously processed file hashes

## Key Implementation Details

### Search Query System
The application uses GitHub's code search API with custom queries from `data/queries.txt`. Query design is critical for effectiveness - use GitHub search syntax with operators like `in:file`, `filename:`, `language:`, etc.

### Key Extraction Logic
- **Gemini keys**: Regex pattern `AIzaSy[A-Za-z0-9\-_]{33}` with placeholder filtering
- **ModelScope keys**: UUID pattern `ms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` with base URL context requirement
- **OpenRouter keys**: Pattern `sk-or-v1-[0-9a-f]{64}` with base URL context requirement

### **NEW**: API Key Validation System
The application now supports real-time validation for all three API key types:

#### Gemini Validation (`src/validators/gemini.py`)
- Uses Google's GenerativeAI client to test keys
- Minimal cost validation using `gemini-2.5-flash` model
- Handles quota limits, service disabling, and network errors
- Returns detailed status: valid, unauthorized, quota_exceeded, service_disabled

#### OpenRouter Validation (`src/validators/openrouter.py`)
- Tests keys via OpenRouter's chat completions API
- Uses free models (e.g., `deepseek/deepseek-chat-v3.1:free`) to minimize cost
- Comprehensive error handling for rate limits and model availability
- Returns validation metadata including model used and token consumption

#### ModelScope Validation (`src/validators/modelscope.py`)
- Validates via ModelScope's chat completions API
- Uses lightweight models like `Qwen/Qwen2-1.5B-Instruct`
- Handles various error conditions: unauthorized, forbidden, rate limits
- Distinguishes between key invalidity and model availability issues

#### Validation Configuration
All validators support:
- Configurable timeout settings
- Proxy support for rate limit avoidance
- Retry mechanisms with exponential backoff
- Detailed error reporting and classification

### Rate Limiting & Resilience
- Automatic GitHub token rotation
- Proxy rotation support
- Exponential backoff on rate limits
- Checkpoint-based resume capability

## **NEW**: Scanning Modes & Validation

The application supports multiple scanning modes for flexible operation:

### Mode Options
- `--mode compatible`: **Full scanning with complete validation** (all three key types)
- `--mode gemini-only`: **Gemini-focused** with validation
- `--mode openrouter-only`: **OpenRouter-focused** with validation
- `--mode modelscope-only`: **ModelScope-focused** with validation

### Quick Launch Options
```bash
# Python quick launcher
python scripts/quick_launch.py [gemini|openrouter|modelscope|all]

# Shell scripts (Linux/Mac)
./scripts/quick_scan.sh [gm|or|ms|all]

# Windows batch
scripts\quick_scan.bat [gm|or|ms|all]
```

### Configuration Presets
Pre-configured environment files in `config/presets/`:
- `gemini-only.env`: Gemini-focused configuration
- `openrouter-only.env`: OpenRouter-focused configuration  
- `modelscope-only.env`: ModelScope-focused configuration

Load with: `python -m src.main --config-preset <preset-name>`

## Testing & Quality

Currently no automated test suite exists. Manual testing workflow:
1. Configure test environment with `.env`
2. Run with `--mode compatible` for full functionality test
3. Verify output files are generated correctly
4. Check logs for proper error handling

When implementing new features, ensure compatibility with the checkpoint system and maintain the modular architecture.
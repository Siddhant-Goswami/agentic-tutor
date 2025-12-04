# Utility Scripts

This directory contains utility scripts for development, testing, and maintenance tasks.

## Available Scripts

### Development & Testing

**`test_ingestion.py`** (formerly `quick_test_ingestion.py`)
- Quick test for content ingestion pipeline
- Usage: `python scripts/test_ingestion.py`

**`setup_and_test.py`**
- Complete setup and testing workflow
- Usage: `python scripts/setup_and_test.py`

### Maintenance

**`run_ingestion.py`**
- Run full content ingestion from RSS feeds
- Usage: `python scripts/run_ingestion.py`
- Requires: Valid Supabase and OpenAI credentials

**`run_migration.py`**
- Run database migrations
- Usage: `python scripts/run_migration.py`
- Requires: Supabase credentials

## Usage Guidelines

### Prerequisites
All scripts require:
1. Python 3.10+
2. Dependencies installed (`pip install -e learning-coach-mcp`)
3. `.env` file configured (see `SETUP_GUIDE.md`)

### Running Scripts

From project root:
```bash
# Run any script
python scripts/<script_name>.py

# Example: Run ingestion
python scripts/run_ingestion.py
```

### Environment Variables

Most scripts require:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `OPENAI_API_KEY` - Your OpenAI API key
- `DEFAULT_USER_ID` - Test user ID (optional)

See `.env.example` for complete list.

## Adding New Scripts

When adding new utility scripts:
1. Place them in this directory
2. Add clear docstrings
3. Update this README
4. Use consistent naming: `<verb>_<noun>.py`

---

**Last Updated:** 2025-12-04

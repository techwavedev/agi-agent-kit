# NotebookLM Configuration Reference

## Environment Variables

Optional `.env` file in the skill directory:

```env
HEADLESS=false           # Browser visibility (true = headless)
SHOW_BROWSER=false       # Default browser display for queries
STEALTH_ENABLED=true     # Human-like typing behavior
TYPING_WPM_MIN=160       # Minimum typing speed (words per minute)
TYPING_WPM_MAX=240       # Maximum typing speed
DEFAULT_NOTEBOOK_ID=     # Default notebook ID (skip activate step)
```

## Virtual Environment

The `.venv` is automatically managed by `run.py`. Manual setup only if automatic fails:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m patchright install chromium
```

## Data Cleanup

```bash
python scripts/run.py cleanup_manager.py                    # Preview cleanup
python scripts/run.py cleanup_manager.py --confirm          # Execute cleanup
python scripts/run.py cleanup_manager.py --preserve-library # Keep notebook library
```
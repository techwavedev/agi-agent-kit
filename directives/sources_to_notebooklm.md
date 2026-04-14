# Sources → NotebookLM Ingest Pipeline

## Goal

Fetch content from configured sources (X, YouTube, RSS, …), deduplicate,
format into Markdown rollups, and upload to Google NotebookLM notebooks —
fully automated, idempotent, and observable.

## Inputs

| Input | Location | Description |
|-------|----------|-------------|
| Source config | `config/ingest_sources.json` | Enabled sources with handles, notebooks, schedules |
| Config schema | `config/ingest_sources.schema.json` | JSON Schema for validation |
| Cookie jar (X) | `.tmp/ingest/x_cookies.json` | Logged-in cookies for twscrape |
| Dedup DB | `.tmp/ingest/seen.db` | SQLite tracking pushed items |

## Tools (Execution Scripts)

| Script | Purpose |
|--------|---------|
| `execution/ingest_dispatcher.py` | Orchestrate full pipeline: fetch → dedup → format → handoff |
| `execution/ingest_config.py` | Load + validate config, warn on issues |
| `execution/source_fetchers/x_fetcher.py` | Fetch tweets via twscrape |
| `execution/source_fetchers/youtube_fetcher.py` | Fetch videos via yt-dlp |
| `execution/ingest_dedup.py` | SQLite dedup: filter_new / mark_pushed |
| `execution/format_items_for_notebooklm.py` | Dispatch to per-type formatters |
| `execution/ensure_notebook.py` | Resolve notebook name → ID (create if missing) |
| `execution/add_source.py` | Upload formatted Markdown to notebook |

## Execution Steps

```
1. Load config
   python3 execution/ingest_config.py --validate config/ingest_sources.json

2. For each enabled source:
   a. Fetch items
      python3 execution/ingest_dispatcher.py run-one <source_id>
   b. Dedup against seen.db
   c. Format → .tmp/ingest/<source_id>/<timestamp>.md
   d. For each notebook in source.notebooks:
      - ensure_notebook (resolve name → ID)
      - add_source (upload .md artifact)
      - mark_pushed in dedup DB

3. Or run all at once:
   python3 execution/ingest_dispatcher.py run

4. Dry-run (no uploads):
   python3 execution/ingest_dispatcher.py dry-run

5. Validate config only:
   python3 execution/ingest_dispatcher.py validate
```

## Outputs

| Output | Location | Description |
|--------|----------|-------------|
| Markdown rollups | `.tmp/ingest/<source_id>/<ts>.md` | Formatted content per source |
| Media files | `.tmp/ingest/media/<type>/<id>/` | Downloaded images/thumbnails |
| JSON handoffs | stdout | `{source_id, notebook, artifact_path, item_count}` per upload |
| Dedup state | `.tmp/ingest/seen.db` | Updated with newly pushed items |

## Edge Cases

### Cookie Expiry (X)
- twscrape will fail to resolve user or fetch tweets
- XFetcher logs error + broadcasts via cross-agent context
- Pipeline continues with remaining sources (per-source failure isolation)
- **Action:** Re-export browser cookies to `.tmp/ingest/x_cookies.json`

### Rate Limiting
- Source fetchers handle rate limits internally (backoff/retry)
- Dispatcher respects per-source `config.rate_limit_delay` if set
- First-run backfill with large date ranges: fetcher pages with delays

### Selector/API Changes
- YouTube: yt-dlp auto-updates; fetcher logs failures and continues
- X: twscrape tracks Twitter API changes; update via `pip install -U twscrape`

### Notebook Not Found
- `ensure_notebook` creates notebook if it doesn't exist
- If creation fails (auth/quota), logs error and skips source

### Duplicate Content
- `ingest_dedup.py` tracks `(source_type, external_id)` in SQLite
- `filter_new()` returns only unseen items
- `mark_pushed()` records successful uploads
- Safe to re-run: idempotent by design

### Config Validation Failures
- `ingest_config.py` validates against JSON Schema
- Warns on: missing required fields, unknown source types, disabled sources
- `validate` subcommand exits non-zero on fatal errors

## Opt-Outs

- Set `"enabled": false` on any source in config to skip it
- Use `run-one <id>` to process a single source
- Use `dry-run` to preview without uploading
- Set `include_media: false` in source config to skip media downloads

## Scheduling

- Manual: run dispatcher on-demand
- Automated: `execution/ingest_scheduler.py` (cron-like, per-source schedules)
- CI: GitHub Actions workflow can trigger on schedule

## Observability

- All scripts emit structured JSON to stdout
- Errors logged to stderr with source context
- Cross-agent broadcasts on critical failures (cookie expiry, auth issues)
- Dedup DB queryable for audit: `SELECT * FROM seen_items WHERE source_type='x'`

---
name: uae-exchange-intelligence
description: Use when building or operating UAE exchange intelligence, market-hours refresh, filings/news ingestion, stock AI research signals, or ADX/DFM data-provider work.
---

# UAE Exchange Intelligence Skill

## Operating Boundary

- Official exchange and issuer sources come first.
- Market data rights are a launch blocker until a licensed/approved provider is connected.
- Do not call quote APIs during market close unless explicitly forced.
- Never label public-delayed, cached, stale, or demo data as live.
- AI output is research support, not personalized financial advice.

## Default Market Clock

- Timezone: `Asia/Dubai`
- Trading days: Monday-Friday
- Pre-open: 09:30-10:00
- Continuous trading: 10:00-14:45
- Closing auction / trade at last: 14:45-15:00
- Quote refreshes happen only in continuous trading unless `--force` is used.

## Core Run Commands

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
bash tools/refresh_live.sh
python3 -m agents.mizan_codex.agent --all --provider ollama --model gemma4:31b-cloud --allow-fallback
bash tools/build.sh
```

## Data Flow

```text
tools/update_live.py  -> data/live_quotes.json + data/provider_status.json
tools/update_news.py  -> data/news.json + data/provider_status.json
tools/refresh_status.py -> data/refresh_job.json
brain/pipeline.py     -> web/data/app_data.json
web/js/app.js         -> market status, frozen quotes, news view, AI signal
```

## Agent Task Brief

For each stock:

1. Read normalized app data.
2. Read local filings.
3. Read real news metadata and source links.
4. Separate official facts, news context, opinion, and AI interpretation.
5. Evaluate accounts, dividends, trend, sector, and global factors.
6. Produce signal label, buy zone, target, invalidation, confidence, and evidence.
7. Add review flags when data is stale, demo, unlicensed, or contradictory.

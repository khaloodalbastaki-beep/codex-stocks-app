# UAE Stocks Intelligence

Isolated Codex build from `/Users/khalidalbastaki/Downloads/UAE Equities Intelligence App Blueprint.docx`.

This folder is intentionally self-contained and separate from any Claude lane or `/Users/khalidalbastaki/Projects/uae-stocks`.

## What It Is

A static bilingual PWA for UAE public-market intelligence:

- ADX / DFM market dashboard
- Stock pages with Overview, News and Disclosures, Meetings, Financials, Dividends, Ownership, Global Factors, and AI Analysis tabs
- Deterministic Growth / Stability / Dividend scores
- Arabic originals plus app-generated translation labels
- Favorite stocks and alert-rule flow stored locally
- Admin diagnostics and launch-readiness guardrails
- Mock provider contract so real delayed/licensed feeds can be swapped later

The app is research support only. It is not brokerage execution and not personalized investment advice.

## Architecture

Khalid ecosystem shape:

```text
Python brain -> normalized JSON -> static PWA -> optional GitHub Pages / GitHub-as-DB later
```

Numbers are owned by deterministic code in `brain/`. The UI reads `web/data/app_data.json`. The AI Analysis tab in this isolated build is deterministic research-support copy generated from scores and evidence fields; no external model is called.

## Run

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
bash tools/build.sh
python3 -m http.server 8821 --directory web
```

Open:

```text
http://localhost:8821
```

## Keep Data Updated

Manual refresh:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
bash tools/refresh_live.sh
```

Install the 5-minute Mac refresh job:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
bash tools/install_refresh_agent.sh
```

The quote updater checks the UAE market clock. When the market is closed, it skips quote API calls and keeps the last published prices frozen. News metadata still refreshes from RSS.

## Test

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
python3 -m unittest discover -s tests
```

## Data Quality

Everything price-like and financial in this isolated build is demo data and is tagged as such. Real tickers and company names are used to make the workflow realistic, but the mock adapter must be replaced with an approved delayed/licensed provider before public launch.

## Provider Boundary

Future providers should implement the normalized adapter shape in `brain/adapters/base.py` and emit the same JSON contract:

- `securities[].quote`
- `securities[].scores`
- `events[]`
- `source_providers[]`
- `admin.launch_readiness[]`

The frontend should not know whether the data came from ADX, DFM, issuer IR, World Bank, GDELT, or a licensed vendor.

## Mizan Codex Agent

The stock-research agent lives at:

```text
agents/mizan_codex
```

Default model lane: Ollama Cloud through the local Ollama API.

```bash
ollama signin
ollama pull gpt-oss:120b-cloud
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider ollama --model gpt-oss:120b-cloud --allow-fallback --print
bash tools/build.sh
```

The agent reads `web/data/app_data.json` and local snippets in `filings/inbox/`, then writes `agent_out/mizan_codex_reports.json`. The PWA shows the latest report in the stock AI Analysis tab and the agent command in Admin.

## Compliance Guardrails

The app visibly separates:

- Official facts
- Media
- Opinion
- AI interpretation

Launch blockers are shown in Admin:

- Market data redistribution rights
- Final SCA / legal wording sign-off

## Project Map

- `brain/registry.py` — seed universe, provider list, exposure definitions
- `brain/scoring.py` — deterministic scoring formulas
- `brain/pipeline.py` — JSON contract builder
- `web/` — static PWA
- `tests/` — scoring, pipeline, and contract tests
- `docs/` — blueprint interpretation and architecture notes

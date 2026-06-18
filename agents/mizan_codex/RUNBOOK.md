# Mizan Codex Runbook

Mizan Codex lives here:

```text
/Users/khalidalbastaki/Documents/codex stocks app/agents/mizan_codex
```

It reads:

```text
web/data/app_data.json
filings/inbox/
```

It writes:

```text
agent_out/mizan_codex_reports.json
```

## What It Does

For each UAE stock, it studies:

- money and accounts from the normalized financial/dividend fields
- official disclosure events already in the app contract
- local filing snippets you drop into `filings/inbox/`
- market trend and global-factor exposure
- positive/negative drivers
- alerts Hermes or the app should care about

It returns a structured research-support report. It does not issue personal buy/sell advice.

## Run With Ollama Cloud From The Mac

Sign in to Ollama if needed, then pull the cloud model:

```bash
ollama signin
ollama pull gpt-oss:120b-cloud
```

Run one stock:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider ollama --model gpt-oss:120b-cloud --allow-fallback --print
bash tools/build.sh
```

Run every stock:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
python3 -m agents.mizan_codex.agent --all --provider ollama --model gpt-oss:120b-cloud --allow-fallback
bash tools/build.sh
```

## Run Deterministic Stub

Useful for testing without any model:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider stub --print
bash tools/build.sh
```

## Optional Free Cloud LLMs

If you want a free-tier cloud model, add one key locally in `.env` or your shell. Do not commit keys.

Gemini:

```bash
export GEMINI_API_KEY="..."
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider gemini --model gemini-1.5-flash --allow-fallback --print
```

Groq:

```bash
export GROQ_API_KEY="..."
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider groq --model llama-3.1-8b-instant --allow-fallback --print
```

OpenRouter:

```bash
export OPENROUTER_API_KEY="..."
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider openrouter --model meta-llama/llama-3.1-8b-instruct:free --allow-fallback --print
```

## Filing Inbox

Drop text, markdown, html, or JSON snippets here:

```text
filings/inbox/
```

Naming convention:

```text
EMAAR-board-meeting-2026-06-18.txt
FAB-results-q1-2026.md
```

The agent only reads local snippets. PDF support should be added later through a deterministic extractor before LLM use.

## Hermes Handoff

To send a safe-capture message to Hermes:

```bash
cd "/Users/khalidalbastaki/Documents/codex stocks app"
python3 -m agents.mizan_codex.agent --symbol EMAAR --provider ollama --model gpt-oss:120b-cloud --allow-fallback --send-hermes
```

This writes a message to:

```text
/Volumes/Samsung_SSD_970_EVO_Plus_Media/Khalid OS/_Bus/inbox/hermes/
```

Use this when you want Hermes to consume the report and update its briefing layer.

## The Exact Task Brief For The Agent

You are Mizan Codex. For each stock:

1. Read the normalized app contract.
2. Read any local filing snippets matching the symbol.
3. Separate official facts, issuer/IR material, media, opinion, and AI interpretation.
4. Study money/accounts: revenue trend, profit trend, margin direction, cash generation, dividend sustainability, payout ratio, and score changes.
5. Study stock-market trend context: price move, sector pulse, global factor exposure, and latest mapped events.
6. Produce a research stance: Bullish, Neutral, Cautious, or Needs Review.
7. Explain what changed, positive drivers, negative drivers, watch items, and alert rules.
8. Cite evidence and review flags.
9. Never invent missing values.
10. Never call it personalized financial advice.

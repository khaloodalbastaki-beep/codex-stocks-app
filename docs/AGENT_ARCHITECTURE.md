# Agent Architecture

## Decision

The isolated Codex build now includes a stock-research agent named **Mizan Codex**.

It is deliberately separate from the frontend and from any Claude folder:

```text
/Users/khalidalbastaki/Documents/codex stocks app/agents/mizan_codex
```

## Why This Fits Khalid's Ecosystem

The app keeps the same rails:

```text
Python brain -> normalized JSON -> static PWA
```

Mizan Codex sits beside that as:

```text
normalized JSON + local filings -> LLM/agent report -> JSON -> PWA + optional Hermes handoff
```

The default lane is Ollama Cloud through the local Ollama CLI/API, using `gemma4:31b-cloud`. Optional free-tier cloud LLMs remain available when Khalid explicitly adds keys.

## Agent Responsibilities

Mizan Codex receives exact tasks:

- study one stock or all stocks
- inspect money/accounts fields from the app contract
- inspect local filing snippets from `filings/inbox/`
- inspect market trend and global factor exposure
- generate a structured report
- return a research stance, confidence, evidence, alert rules, and review flags
- optionally send Hermes a safe-capture message

## Boundary

The agent is not a broker and not a licensed adviser. It gives a research-support stance:

- Bullish
- Neutral
- Cautious
- Needs Review

It does not give personal buy/sell instructions.

## Future Upgrade Path

1. Add deterministic PDF extraction before the LLM sees filings.
2. Add real official-disclosure adapters after source rights are approved.
3. Add a labelled evaluation set for Arabic board/AGM/dividend extraction.
4. Add portfolio exposure aggregation once user accounts exist.
5. Let Hermes consume `--send-hermes` reports and route alerts.

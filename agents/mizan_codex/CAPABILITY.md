# Capability Card — Mizan Codex

- **Agent id:** `mizan-codex`
- **Role:** UAE equities research-support agent
- **Home:** `/Users/khalidalbastaki/Documents/codex stocks app/agents/mizan_codex`
- **Inputs:** normalized app data, local filing snippets, optional LLM provider
- **Outputs:** structured stock reports in `agent_out/mizan_codex_reports.json`
- **Default model lane:** Ollama Cloud through Khalid's Mac, currently `gemma4:31b-cloud`
- **Optional free cloud lanes:** Gemini, Groq, OpenRouter
- **Hermes integration:** optional safe-capture bus handoff with `--send-hermes`
- **Boundary:** research support only, not personalized financial advice

## Best Tasks For This Agent

- "Study EMAAR and tell me what changed."
- "Run all watchlist stocks and tell Hermes what deserves an alert."
- "Read this board meeting filing and extract the dividend/governance implications."
- "Compare score movement versus latest filing evidence."
- "List risk flags before I trust the AI stance."

# ADR-0001: Mizan Codex Ollama Cloud Model

**Status:** Accepted
**Date:** 2026-06-18
**Deciders:** Khalid, Codex

## Context

Mizan Codex needs a cloud LLM that runs through Ollama on Khalid's Mac. The agent must study UAE stocks, local filings, real-news metadata, market trend fields, and deterministic price signals without moving the app into a Claude folder or a separate project.

## Decision

Use `gemma4:31b-cloud` as the default Ollama Cloud model for Mizan Codex because it is an Ollama Cloud model that the current account can actually run.

## Options Considered

### Option A: `gemma4:31b-cloud`

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Accessible on current account |
| Context | Cloud-hosted long-context model |
| Fit | Strong current default for stock research summaries |

**Pros:** Verified through the local Ollama API, avoids the rejected `gpt-oss` lane, and keeps the agent on the Mac-driven Ollama path.
**Cons:** Not the preferred Hermes-style model if the account later unlocks Kimi.

### Option B: `gemma3:27b-cloud`

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Accessible on current account |
| Context | Smaller cloud model |
| Fit | Backup lane |

**Pros:** Also returned successfully through the local Ollama API.
**Cons:** Smaller than Gemma 4.

### Option C: `kimi-k2.6:cloud`

| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | Requires subscription upgrade on this account |
| Context | 256K |
| Fit | Preferred future Hermes-style agent lane |

**Pros:** Long context, tool/thinking capabilities, good match for a persistent stock-research agent.
**Cons:** The current account returned HTTP 403 subscription-required.

## Consequences

- The default command is now `--model gemma4:31b-cloud`.
- The app still supports overriding `MIZAN_MODEL` without code changes.
- `gemma3:27b-cloud` is the accessible fallback.
- `kimi-k2.6:cloud`, `qwen3.5:cloud`, `glm-5.1:cloud`, and `deepseek-v4-pro:cloud` remain comparison candidates after subscription access changes.

## Action Items

1. Use Gemma 4 Cloud for the next Mizan reports.
2. Keep deterministic validation and fallback around every LLM response.
3. Compare Gemma 4 against Kimi after the Ollama subscription tier is unlocked.

# Architecture

## Contract First

The app is built around a single generated contract:

```text
data/app_data.json
```

The PWA does not call a vendor. It reads normalized objects:

- `metadata`
- `market_pulse`
- `securities`
- `events`
- `global_signals`
- `source_providers`
- `admin`

This preserves the separation requested in the blueprint: data collection can change without rewriting the investor workflow.

## Deterministic Brain

`brain/scoring.py` owns the numeric model:

- Growth score
- Stability score
- Dividend score
- Composite score
- Stance and confidence band

LLM-style text in this demo is generated from deterministic fields. A future structured-output model should only extract/summarize/classify evidence into validated JSON; it should not invent scores.

## Frontend

The frontend is a dependency-free static PWA:

- `web/index.html`
- `web/css/app.css`
- `web/js/app.js`
- `web/js/charts.js`
- `web/js/i18n.js`

Routes are hash-based so the app can run from any static host:

- `#/`
- `#/markets/adx`
- `#/markets/dfm`
- `#/stocks/{symbol}`
- `#/watchlist`
- `#/alerts`
- `#/screeners`
- `#/global-factors`
- `#/ipos`
- `#/admin`

## Future Integrations

Provider swaps should happen behind `brain/adapters/`:

- Official exchange disclosures
- Corporate actions calendars
- Issuer IR reports
- World Bank commodity series
- GDELT global event feed
- Licensed delayed or real-time exchange market data

Before public launch, market-data rights and SCA/legal wording must be resolved.


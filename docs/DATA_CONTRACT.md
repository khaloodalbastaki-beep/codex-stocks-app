# Data Contract

## Security

```json
{
  "symbol": "EMAAR",
  "isin": "AEE000301011",
  "name_en": "Emaar Properties",
  "name_ar": "إعمار العقارية",
  "exchange": "DFM",
  "sector": "Real Estate",
  "quote": {
    "last_price": 13.65,
    "change_pct": 1.7,
    "data_quality": "demo",
    "status_label": "Demo delayed"
  },
  "scores": {
    "growth": 86,
    "stability": 68,
    "dividend": 71,
    "composite": 75
  }
}
```

## Event

```json
{
  "source_type": "official_exchange",
  "event_type": "board_meeting",
  "title_en": "Board meeting scheduled...",
  "title_ar": "اجتماع مجلس الإدارة...",
  "summary": "Short summary",
  "why_it_matters": "Investor-relevant explanation",
  "materiality": 78,
  "sentiment": "Positive",
  "evidence": ["DFM official disclosure"]
}
```

Official filing events may also include source links:

```json
{
  "source_url": "https://www.dfm.ae/the-exchange/news-disclosures/disclosures",
  "document_url": "https://feeds.dfm.ae/documents/...",
  "data_quality": "official_metadata",
  "signals": ["financial_statements", "dividend_policy"]
}
```

## Launch Readiness

```json
{
  "id": "data_rights",
  "label": "Market data rights",
  "status": "blocked",
  "note": "Real-time redistribution needs licensed feed or exchange approval."
}
```

const App = {
  data: null,
  lang: localStorage.getItem("uae-lang") || "en",
  theme: localStorage.getItem("uae-theme") || "light",
  favorites: new Set(JSON.parse(localStorage.getItem("uae-favorites") || '["EMAAR","FAB","DEWA","SALIK"]')),
  alerts: JSON.parse(localStorage.getItem("uae-alerts") || "[]"),
  activeTab: "overview",
  analysisRuns: new Set()
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const fmt = new Intl.NumberFormat("en-AE", { maximumFractionDigits: 2 });
const pct = (value) => `${value > 0 ? "+" : ""}${Number(value).toFixed(1)}%`;

function t(key) {
  return (window.UAE_I18N[App.lang] && window.UAE_I18N[App.lang][key]) || window.UAE_I18N.en[key] || key;
}

function saveState() {
  localStorage.setItem("uae-favorites", JSON.stringify([...App.favorites]));
  localStorage.setItem("uae-alerts", JSON.stringify(App.alerts));
  localStorage.setItem("uae-lang", App.lang);
  localStorage.setItem("uae-theme", App.theme);
}

function security(symbol) {
  return App.data.securities.find((item) => item.symbol === symbol) || App.data.securities[0];
}

function route() {
  const hash = window.location.hash || "#/";
  const path = hash.replace("#", "");
  if (path.startsWith("/stocks/")) return renderStock(path.split("/").pop());
  if (path === "/markets/adx") return renderMarket("ADX");
  if (path === "/markets/dfm") return renderMarket("DFM");
  if (path === "/watchlist") return renderWatchlist();
  if (path === "/alerts") return renderAlerts();
  if (path === "/screeners") return renderScreeners();
  if (path === "/global-factors") return renderGlobalFactors();
  if (path === "/ipos") return renderIpos();
  if (path === "/admin") return renderAdmin();
  return renderHome();
}

function initChrome() {
  document.documentElement.dataset.theme = App.theme;
  document.documentElement.lang = App.lang;
  document.documentElement.dir = App.lang === "ar" ? "rtl" : "ltr";
  $("#nav").innerHTML = [
    ["#/", "nav_home", iconHome()],
    ["#/markets/adx", "nav_adx", iconExchange()],
    ["#/markets/dfm", "nav_dfm", iconExchange()],
    ["#/watchlist", "nav_watchlist", iconStar()],
    ["#/alerts", "nav_alerts", iconBell()],
    ["#/screeners", "nav_screeners", iconFilter()],
    ["#/global-factors", "nav_factors", iconGlobe()],
    ["#/ipos", "nav_ipos", iconCalendar()],
    ["#/admin", "nav_admin", iconSettings()]
  ]
    .map(([href, key, icon]) => `<a href="${href}" class="nav-link" data-href="${href}">${icon}<span>${t(key)}</span></a>`)
    .join("");
  $("#marketStatus").innerHTML = `
    <strong>${t("delayed_demo")}</strong>
    <span>Official-first architecture. Demo market data. ${t("not_advice")}.</span>
    <span>${new Date(App.data.metadata.build_time).toLocaleString()}</span>`;
  $("#langToggle").textContent = App.lang === "en" ? "عربي" : "English";
}

function bindGlobalActions() {
  $("#themeToggle").addEventListener("click", () => {
    App.theme = App.theme === "light" ? "dark" : "light";
    saveState();
    initChrome();
  });
  $("#langToggle").addEventListener("click", () => {
    App.lang = App.lang === "en" ? "ar" : "en";
    saveState();
    initChrome();
    route();
  });
  $("#search").addEventListener("input", (event) => renderSearch(event.target.value.trim()));
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-wrap")) $("#searchResults").hidden = true;
    const fav = event.target.closest("[data-favorite]");
    if (fav) toggleFavorite(fav.dataset.favorite);
    const alert = event.target.closest("[data-alert]");
    if (alert) addAlert(alert.dataset.alert, alert.dataset.type || "disclosure");
    const tab = event.target.closest("[data-tab]");
    if (tab) {
      App.activeTab = tab.dataset.tab;
      renderStock(tab.dataset.symbol);
    }
    const analyze = event.target.closest("[data-analyze]");
    if (analyze) {
      App.analysisRuns.add(analyze.dataset.analyze);
      renderStock(analyze.dataset.analyze);
    }
  });
  window.addEventListener("hashchange", route);
}

function renderSearch(query) {
  const box = $("#searchResults");
  if (!query) {
    box.hidden = true;
    return;
  }
  const q = query.toLowerCase();
  const rows = App.data.securities
    .filter((item) => `${item.symbol} ${item.name_en} ${item.name_ar} ${item.sector}`.toLowerCase().includes(q))
    .slice(0, 8);
  box.innerHTML = rows
    .map(
      (item) => `<a href="#/stocks/${item.symbol}">
        <strong>${item.symbol}</strong><span>${nameOf(item)}</span><small>${item.exchange} · ${item.sector}</small>
      </a>`
    )
    .join("");
  box.hidden = rows.length === 0;
}

function renderHome() {
  setActive("#/");
  const favorites = App.data.securities.filter((item) => App.favorites.has(item.symbol)).slice(0, 6);
  const featured = security("EMAAR");
  $("#view").innerHTML = `
    <section class="hero-grid">
      <div class="panel hero-panel">
        <div class="section-head">
          <div>
            <h1>UAE Stocks Intelligence</h1>
            <p>Official-first market intelligence for ADX and DFM equities, with Arabic originals, evidence-linked summaries, and deterministic house scores.</p>
          </div>
          <a class="primary-button" href="#/stocks/${featured.symbol}">${t("ai_support")}</a>
        </div>
        <h2>${t("market_pulse")}</h2>
        <div class="pulse-grid">${App.data.market_pulse.map(marketPulseCard).join("")}</div>
      </div>
      <aside class="panel insight-panel">
        ${selectedInsight(featured)}
      </aside>
    </section>

    <section class="dashboard-grid">
      <div class="panel span-2">
        <div class="section-head compact">
          <h2>${t("favorite_stocks")}</h2>
          <a href="#/watchlist">View all</a>
        </div>
        <div class="stock-grid">${favorites.map(stockCard).join("")}</div>
      </div>
      <div class="panel">
        <div class="section-head compact"><h2>${t("events")}</h2><a href="#/alerts">Create alerts</a></div>
        <div class="timeline">${App.data.events.slice(0, 5).map(eventRow).join("")}</div>
      </div>
      <div class="panel span-2">
        <div class="section-head compact"><h2>${t("latest_disclosures")}</h2><a href="#/screeners">Filter</a></div>
        <div class="disclosure-list">${App.data.events.slice(0, 5).map(disclosureRow).join("")}</div>
      </div>
      <div class="panel">
        <div class="section-head compact"><h2>${t("global_factors")}</h2><a href="#/global-factors">Open map</a></div>
        <div class="factor-list">${globalFactorRows().slice(0, 6).join("")}</div>
      </div>
    </section>`;
}

function renderMarket(exchange) {
  setActive(exchange === "ADX" ? "#/markets/adx" : "#/markets/dfm");
  const rows = App.data.securities.filter((item) => item.exchange === exchange);
  $("#view").innerHTML = `
    <section class="page-head">
      <h1>${exchange} market</h1>
      <p>${rows.length} demo securities. Provider swap-ready; data quality remains visible.</p>
    </section>
    <section class="stock-grid market-grid">${rows.map(stockCard).join("")}</section>`;
}

function renderWatchlist() {
  setActive("#/watchlist");
  const rows = App.data.securities.filter((item) => App.favorites.has(item.symbol));
  $("#view").innerHTML = `
    <section class="page-head">
      <h1>${t("nav_watchlist")}</h1>
      <p>Favorites are stored locally in this browser. This is ready for a GitHub-as-DB sync lane later.</p>
    </section>
    <section class="stock-grid market-grid">${rows.map(stockCard).join("")}</section>`;
}

function renderAlerts() {
  setActive("#/alerts");
  $("#view").innerHTML = `
    <section class="page-head">
      <h1>${t("nav_alerts")}</h1>
      <p>Alert rules for disclosures, meetings, dividends, IPOs, factor shocks, and AI view changes.</p>
    </section>
    <section class="dashboard-grid">
      <div class="panel">
        <h2>Create a rule</h2>
        <div class="rule-grid">
          ${["disclosure", "board meeting", "AGM", "dividend", "global factor", "AI view changed"]
            .map((type) => `<button class="rule-button" data-alert="EMAAR" data-type="${type}">${type}</button>`)
            .join("")}
        </div>
      </div>
      <div class="panel span-2">
        <h2>Active rules</h2>
        <div class="table">${alertRows()}</div>
      </div>
    </section>`;
}

function renderScreeners() {
  setActive("#/screeners");
  const income = App.data.securities.filter((item) => item.scores.dividend >= 68).sort((a, b) => b.scores.dividend - a.scores.dividend);
  const growth = App.data.securities.filter((item) => item.scores.growth >= 72).sort((a, b) => b.scores.growth - a.scores.growth);
  $("#view").innerHTML = `
    <section class="page-head"><h1>${t("nav_screeners")}</h1><p>Deterministic screeners from house scores, not LLM guesses.</p></section>
    <section class="dashboard-grid">
      <div class="panel"><h2>Income quality</h2><div class="compact-list">${income.map(compactSecurityRow).join("")}</div></div>
      <div class="panel"><h2>Growth leaders</h2><div class="compact-list">${growth.map(compactSecurityRow).join("")}</div></div>
      <div class="panel"><h2>Cautious watch</h2><div class="compact-list">${App.data.securities.filter((item) => item.stance === "Cautious").map(compactSecurityRow).join("")}</div></div>
    </section>`;
}

function renderGlobalFactors() {
  setActive("#/global-factors");
  $("#view").innerHTML = `
    <section class="page-head">
      <h1>${t("global_factors")}</h1>
      <p>Maps macro and commodity moves to company exposure. Every impact keeps evidence and confidence visible.</p>
    </section>
    <section class="factor-map">${App.data.securities.map(factorCard).join("")}</section>`;
}

function renderIpos() {
  setActive("#/ipos");
  $("#view").innerHTML = `
    <section class="page-head"><h1>${t("nav_ipos")}</h1><p>Prepared for IPO windows, subscription dates, allocations, and first-trade alerts.</p></section>
    <section class="panel empty-state">
      <strong>No live IPO provider connected.</strong>
      <p>The contract is ready, but this isolated build uses demo mode until an approved source is connected.</p>
    </section>`;
}

function renderAdmin() {
  setActive("#/admin");
  const admin = App.data.admin;
  $("#view").innerHTML = `
    <section class="page-head">
      <h1>${t("nav_admin")}</h1>
      <p>Source diagnostics, queues, and launch-readiness guardrails.</p>
    </section>
    <section class="dashboard-grid">
      <div class="panel span-2">
        <h2>Launch readiness</h2>
        <div class="readiness-grid">${admin.launch_readiness.map(readinessCard).join("")}</div>
      </div>
      <div class="panel">
        <h2>Queues</h2>
        <div class="queue-list">${admin.queues.map(queueRow).join("")}</div>
      </div>
      <div class="panel span-3">
        <h2>Source providers</h2>
        <div class="table provider-table">${providerRows()}</div>
      </div>
    </section>`;
}

function renderStock(symbol) {
  const item = security(symbol);
  const events = App.data.events.filter((event) => event.symbol === item.symbol);
  setActive("");
  if (!["overview", "news", "meetings", "financials", "dividends", "ownership", "global", "ai"].includes(App.activeTab)) {
    App.activeTab = "overview";
  }
  $("#view").innerHTML = `
    <section class="stock-head panel">
      <div>
        <div class="stock-title-row">
          <h1>${item.symbol}</h1>
          <button class="favorite-button ${App.favorites.has(item.symbol) ? "active" : ""}" data-favorite="${item.symbol}" aria-label="Toggle favorite">${iconStar(true)}</button>
        </div>
        <p>${nameOf(item)} · ${item.exchange} · ${item.sector}</p>
      </div>
      <div class="price-block">
        <strong>${item.quote.currency} ${fmt.format(item.quote.last_price)}</strong>
        <span class="${item.quote.change_pct >= 0 ? "positive" : "negative"}">${pct(item.quote.change_pct)}</span>
        <small>${item.quote.status_label} · ${timeAgo(item.quote.as_of)}</small>
      </div>
    </section>
    <div class="tabs" role="tablist">
      ${[
        ["overview", t("overview")],
        ["news", t("news")],
        ["meetings", t("meetings")],
        ["financials", t("financials")],
        ["dividends", t("dividends")],
        ["ownership", t("ownership")],
        ["global", t("global_factors")],
        ["ai", t("ai_analysis")]
      ]
        .map(([key, label]) => `<button role="tab" class="${App.activeTab === key ? "active" : ""}" data-symbol="${item.symbol}" data-tab="${key}">${label}</button>`)
        .join("")}
    </div>
    <section>${stockTab(item, events)}</section>`;
}

function stockTab(item, events) {
  if (App.activeTab === "news") {
    return `<div class="panel"><div class="disclosure-list">${events.map(disclosureRow).join("") || empty("No event yet")}</div></div>`;
  }
  if (App.activeTab === "meetings") {
    return `<div class="dashboard-grid">${item.meetings.map(meetingCard).join("")}</div>`;
  }
  if (App.activeTab === "financials") {
    return `<div class="dashboard-grid"><div class="panel">${financialsPanel(item)}</div><div class="panel">${window.UAECharts.bars(item.financials.series)}</div></div>`;
  }
  if (App.activeTab === "dividends") {
    return `<div class="dashboard-grid"><div class="panel">${dividendPanel(item)}</div><div class="panel">${item.dividends.next_dates.map((d) => `<div class="date-row"><strong>${d.label}</strong><span>${d.date}</span></div>`).join("")}</div></div>`;
  }
  if (App.activeTab === "ownership") {
    return `<div class="dashboard-grid"><div class="panel">${ownershipPanel(item)}</div><div class="panel">${foreignOwnershipPanel(item)}</div></div>`;
  }
  if (App.activeTab === "global") {
    return `<div class="factor-map">${item.global_factors.map((factor) => factorPill(factor, true)).join("")}</div>`;
  }
  if (App.activeTab === "ai") {
    return `<div class="dashboard-grid"><div class="panel span-2">${aiPanel(item)}</div><div class="panel">${evidencePanel(item)}</div></div>`;
  }
  return `<div class="dashboard-grid">
    <div class="panel span-2">${overviewPanel(item)}</div>
    <div class="panel">${scorePanel(item)}</div>
    <div class="panel">${riskCatalystPanel(item)}</div>
    <div class="panel span-2">${selectedInsight(item)}</div>
  </div>`;
}

function marketPulseCard(row) {
  return `<article class="pulse-card">
    <span>${row.label}</span>
    <strong>${row.level}</strong>
    <small class="${row.change_pct >= 0 ? "positive" : "negative"}">${pct(row.change_pct)} · ${row.breadth}</small>
  </article>`;
}

function stockCard(item) {
  const series = item.financials.series.map((row) => row.revenue + row.profit / 2);
  return `<article class="stock-card">
    <div class="stock-card-head">
      <a href="#/stocks/${item.symbol}"><strong>${item.symbol}</strong><span>${nameOf(item)}</span></a>
      <button class="favorite-button ${App.favorites.has(item.symbol) ? "active" : ""}" data-favorite="${item.symbol}" aria-label="Toggle favorite">${iconStar(true)}</button>
    </div>
    <div class="stock-price">
      <strong>${item.quote.currency} ${fmt.format(item.quote.last_price)}</strong>
      <span class="${item.quote.change_pct >= 0 ? "positive" : "negative"}">${pct(item.quote.change_pct)}</span>
    </div>
    ${window.UAECharts.sparkline(series, { tone: item.quote.change_pct >= 0 ? "positive" : "negative" })}
    <div class="score-row">
      ${scoreChip(t("score_growth"), item.scores.growth)}
      ${scoreChip(t("score_stability"), item.scores.stability)}
      ${scoreChip(t("score_dividend"), item.scores.dividend)}
    </div>
    <div class="card-foot">
      <span class="impact ${item.impact_chip.toLowerCase()}">${item.impact_chip}</span>
      <small>${item.latest_catalyst}</small>
    </div>
  </article>`;
}

function selectedInsight(item) {
  return `<div class="insight">
    <div class="section-head compact">
      <h2>${t("ai_support")}</h2>
      <span class="badge ai">AI</span>
    </div>
    <strong>${item.symbol}: ${item.stance}</strong>
    <p>${item.analysis.short_term.reasons[0]} ${item.analysis.short_term.reasons[2]}</p>
    <div class="score-stack">
      ${metricBar(t("score_growth"), item.scores.growth)}
      ${metricBar(t("score_stability"), item.scores.stability)}
      ${metricBar(t("score_dividend"), item.scores.dividend)}
    </div>
    <div class="evidence-line"><span>${item.confidence} confidence</span><span>${t("not_advice")}</span></div>
  </div>`;
}

function overviewPanel(item) {
  return `<h2>${t("overview")}</h2>
    <p>${item.summary}</p>
    <div class="quick-grid">
      ${kv("Market cap", `${item.quote.currency} ${fmt.format(item.quote.market_cap_bn)}bn`)}
      ${kv("Volume", `${fmt.format(item.quote.volume_m)}m`)}
      ${kv("Index", item.index_membership.join(", "))}
      ${kv("Data", item.quote.status_label)}
    </div>`;
}

function scorePanel(item) {
  return `<h2>House scores</h2>
    <div class="score-stack">
      ${metricBar(t("score_growth"), item.scores.growth)}
      ${metricBar(t("score_stability"), item.scores.stability)}
      ${metricBar(t("score_dividend"), item.scores.dividend)}
      ${metricBar("Composite", item.scores.composite)}
    </div>`;
}

function riskCatalystPanel(item) {
  return `<h2>Risks and catalysts</h2>
    <h3>Catalysts</h3>
    <div class="chip-list">${item.top_catalysts.map((row) => `<span>${row}</span>`).join("")}</div>
    <h3>Risks</h3>
    <div class="chip-list risk">${item.top_risks.map((row) => `<span>${row}</span>`).join("")}</div>`;
}

function financialsPanel(item) {
  return `<h2>${t("financials")}</h2>
    <div class="quick-grid">
      ${kv("Revenue growth", pct(item.financials.revenue_growth_pct))}
      ${kv("Profit growth", pct(item.financials.profit_growth_pct))}
      ${kv("Margin", item.financials.margin_direction)}
      ${kv("Cash generation", item.financials.cash_generation)}
    </div>
    <p class="muted">Source documents: ${item.financials.source_documents.join(", ")}.</p>`;
}

function dividendPanel(item) {
  return `<h2>${t("dividends")}</h2>
    <div class="quick-grid">
      ${kv("Yield", `${item.dividends.yield_pct.toFixed(1)}%`)}
      ${kv("Frequency", item.dividends.frequency)}
      ${kv("Payout ratio", `${item.dividends.payout_ratio_pct.toFixed(0)}%`)}
      ${kv("Sustainability", item.dividends.sustainability)}
    </div>
    <p class="muted">Dividend score does not treat high yield as automatically good.</p>`;
}

function ownershipPanel(item) {
  return `<h2>${t("ownership")}</h2>${item.ownership.mix.map((row) => metricBar(row.holder, row.pct)).join("")}`;
}

function foreignOwnershipPanel(item) {
  const fo = item.ownership.foreign_ownership;
  return `<h2>Foreign ownership</h2>
    ${metricBar("Permitted", fo.permitted_pct)}
    ${metricBar("Actual", fo.actual_pct)}
    ${metricBar("Available", fo.available_pct)}
    <p class="muted">Demo values. Ready for DFM/ADX ownership provider mapping.</p>`;
}

function aiPanel(item) {
  const run = App.analysisRuns.has(item.symbol);
  return `<div class="section-head compact">
      <h2>${t("ai_analysis")}</h2>
      <button class="primary-button" data-analyze="${item.symbol}">${run ? "Re-run deterministic analysis" : "AI Analyze This Stock"}</button>
    </div>
    ${run ? `<p class="success-note">Analysis refreshed locally from current deterministic data. No external model was called in demo mode.</p>` : ""}
    <div class="analysis-grid">
      ${analysisBlock("Short term direction", item.analysis.short_term)}
      ${analysisBlock("Long term direction", item.analysis.long_term)}
    </div>
    <p class="muted">${item.analysis.label}.</p>`;
}

function analysisBlock(title, block) {
  return `<article class="analysis-block">
    <div class="stance-row"><strong>${title}</strong><span class="impact ${block.stance.toLowerCase()}">${block.stance}</span><small>${block.confidence} confidence</small></div>
    <h3>Reasons</h3>
    <ol>${block.reasons.map((row) => `<li>${row}</li>`).join("")}</ol>
    <h3>Risks</h3>
    <ol>${block.risks.slice(0, 5).map((row) => `<li>${row}</li>`).join("")}</ol>
    <p><strong>What changes the view:</strong> ${block.what_changes_view || "Validated filing changes or a material macro signal."}</p>
  </article>`;
}

function evidencePanel(item) {
  const evidence = item.analysis.long_term.evidence;
  return `<h2>Evidence references</h2>
    <div class="source-stack">${evidence.map((row) => `<span class="badge official">${row}</span>`).join("")}</div>
    <p class="muted">Every derived view must point back to source evidence before public launch.</p>`;
}

function disclosureRow(event) {
  return `<article class="disclosure-row">
    <div>
      <span class="badge ${badgeClass(event.source_type)}">${event.source_type.replace("_", " ")}</span>
      <a href="#/stocks/${event.symbol}"><strong>${event.symbol}</strong> ${event.title_en}</a>
      <p lang="ar" dir="rtl">${event.title_ar}</p>
      <small>${event.source_name} · ${timeAgo(event.timestamp)} · Translation: app generated</small>
    </div>
    <aside>
      <span class="materiality">${event.materiality}</span>
      <span class="impact ${event.sentiment.toLowerCase()}">${event.sentiment}</span>
    </aside>
  </article>`;
}

function eventRow(event) {
  return `<a class="timeline-row" href="#/stocks/${event.symbol}">
    <span>${event.timestamp.slice(5, 10)}</span>
    <strong>${event.symbol}</strong>
    <small>${event.event_type.replace("_", " ")}</small>
  </a>`;
}

function meetingCard(meeting) {
  return `<article class="panel">
    <h2>${meeting.title}</h2>
    <p>${meeting.date} · ${meeting.status} · ${meeting.source}</p>
    <div class="chip-list">${meeting.agenda.map((row) => `<span>${row}</span>`).join("")}</div>
  </article>`;
}

function factorCard(item) {
  return `<article class="panel factor-card">
    <div class="section-head compact"><h2>${item.symbol}</h2><a href="#/stocks/${item.symbol}">Open</a></div>
    <p>${item.summary}</p>
    <div class="factor-list">${item.global_factors.map((factor) => factorPill(factor)).join("")}</div>
  </article>`;
}

function factorPill(factor, large = false) {
  return `<article class="factor-pill ${large ? "large" : ""}">
    <span class="impact ${factor.impact_tag.toLowerCase()}">${factor.impact_tag}</span>
    <strong>${factor.label}</strong>
    <small>${factor.move}</small>
    <p>${factor.impact}</p>
  </article>`;
}

function globalFactorRows() {
  const seen = new Set();
  const rows = [];
  App.data.securities.forEach((item) => {
    item.global_factors.forEach((factor) => {
      if (!seen.has(factor.label)) {
        seen.add(factor.label);
        rows.push(factorPill(factor));
      }
    });
  });
  return rows;
}

function readinessCard(row) {
  return `<article class="readiness-card ${row.status}">
    <span>${row.status}</span>
    <strong>${row.label}</strong>
    <p>${row.note}</p>
  </article>`;
}

function queueRow(row) {
  return `<div class="queue-row"><strong>${row.name}</strong><span class="${row.tone === "ok" ? "positive" : "watch"}">${row.count}</span></div>`;
}

function providerRows() {
  return `
    <div class="table-head"><span>Provider</span><span>Layer</span><span>Status</span><span>Rights posture</span></div>
    ${App.data.source_providers
      .map((row) => `<div class="table-row"><span>${row.name}</span><span>${row.layer}</span><span>${row.status}</span><span>${row.rights_posture}</span></div>`)
      .join("")}`;
}

function alertRows() {
  if (!App.alerts.length) return empty("No active rules yet. Create one from the left.");
  return `
    <div class="table-head"><span>Symbol</span><span>Rule</span><span>Created</span></div>
    ${App.alerts.map((row) => `<div class="table-row"><span>${row.symbol}</span><span>${row.type}</span><span>${row.created.slice(0, 10)}</span></div>`).join("")}`;
}

function compactSecurityRow(item) {
  return `<a class="compact-security" href="#/stocks/${item.symbol}">
    <strong>${item.symbol}</strong><span>${nameOf(item)}</span><small>${item.stance} · ${item.scores.composite}/100</small>
  </a>`;
}

function metricBar(label, value) {
  return `<div class="metric-bar">
    <div><span>${label}</span><strong>${Math.round(value)}</strong></div>
    <i style="width:${Math.max(3, Math.min(100, value))}%"></i>
  </div>`;
}

function scoreChip(label, value) {
  return `<span class="score-chip"><small>${label}</small><strong>${value}</strong></span>`;
}

function kv(label, value) {
  return `<div class="kv"><span>${label}</span><strong>${value}</strong></div>`;
}

function nameOf(item) {
  return App.lang === "ar" ? item.name_ar : item.name_en;
}

function timeAgo(input) {
  const delta = Date.now() - new Date(input).getTime();
  const hours = Math.max(1, Math.round(delta / 36e5));
  return `${hours}h ago`;
}

function badgeClass(sourceType) {
  if (sourceType.includes("official")) return "official";
  if (sourceType.includes("media")) return "media";
  if (sourceType.includes("global")) return "ai";
  return "opinion";
}

function setActive(href) {
  $$(".nav-link").forEach((link) => link.classList.toggle("active", href && link.dataset.href === href));
}

function toggleFavorite(symbol) {
  if (App.favorites.has(symbol)) App.favorites.delete(symbol);
  else App.favorites.add(symbol);
  saveState();
  route();
}

function addAlert(symbol, type) {
  App.alerts.unshift({ symbol, type, created: new Date().toISOString() });
  App.alerts = App.alerts.slice(0, 20);
  saveState();
  renderAlerts();
}

function empty(message) {
  return `<div class="empty-state"><strong>${message}</strong></div>`;
}

function iconHome() { return `<svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5V21h-6v-6H9v6H3Z"/></svg>`; }
function iconExchange() { return `<svg viewBox="0 0 24 24"><path d="M4 20h16M6 16V8m6 8V4m6 12v-6"/></svg>`; }
function iconStar(fill = false) { return `<svg viewBox="0 0 24 24" class="${fill ? "star" : ""}"><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z"/></svg>`; }
function iconBell() { return `<svg viewBox="0 0 24 24"><path d="M18 9a6 6 0 1 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Zm-8 12h4"/></svg>`; }
function iconFilter() { return `<svg viewBox="0 0 24 24"><path d="M4 5h16l-6 7v6l-4 2v-8Z"/></svg>`; }
function iconGlobe() { return `<svg viewBox="0 0 24 24"><path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm-8-9h16M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>`; }
function iconCalendar() { return `<svg viewBox="0 0 24 24"><path d="M7 3v4m10-4v4M4 9h16M5 5h14v16H5Z"/></svg>`; }
function iconSettings() { return `<svg viewBox="0 0 24 24"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm8 4h2M2 12h2m14.4-6.4 1.4-1.4M4.2 19.8l1.4-1.4m0-12.8L4.2 4.2m15.6 15.6-1.4-1.4"/></svg>`; }

async function boot() {
  try {
    const response = await fetch("data/app_data.json", { cache: "no-store" });
    App.data = await response.json();
    initChrome();
    bindGlobalActions();
    route();
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
  } catch (error) {
    $("#view").innerHTML = `<section class="panel empty-state"><strong>Data failed to load.</strong><p>${error.message}</p></section>`;
  }
}

boot();

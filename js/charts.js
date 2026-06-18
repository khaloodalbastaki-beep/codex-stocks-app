window.UAECharts = {
  sparkline(values, options = {}) {
    const width = options.width || 190;
    const height = options.height || 58;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const step = width / (values.length - 1 || 1);
    const points = values
      .map((value, index) => {
        const x = index * step;
        const y = height - ((value - min) / range) * (height - 8) - 4;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
    const tone = options.tone || "positive";
    return `
      <svg class="sparkline ${tone}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Price trend">
        <defs>
          <linearGradient id="spark-${tone}" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="currentColor" stop-opacity=".22" />
            <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
          </linearGradient>
        </defs>
        <polyline points="${points}" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline>
        <polygon points="0,${height} ${points} ${width},${height}" fill="url(#spark-${tone})"></polygon>
      </svg>`;
  },
  bars(rows) {
    const max = Math.max(...rows.flatMap((row) => [row.revenue, row.profit]));
    return `<div class="mini-bars">${rows
      .map(
        (row) => `
          <div class="bar-row">
            <span>${row.period}</span>
            <div class="bar-track"><i style="width:${(row.revenue / max) * 100}%"></i></div>
            <div class="bar-track profit"><i style="width:${(row.profit / max) * 100}%"></i></div>
          </div>`
      )
      .join("")}</div>`;
  }
};


/**
 * Card UI Components
 */

function createStatCard(title, value, subtitle = "") {
  return `
    <div class="card stat-card">
      <div class="stat-title" style="color: var(--text-muted); font-size: 13px; font-weight: 500; text-transform: uppercase;">${title}</div>
      <div class="stat-value" style="font-size: 28px; font-weight: 600; margin: 8px 0;">${value}</div>
      ${subtitle ? `<div class="stat-subtitle" style="font-size: 12px; color: var(--text-muted);">${subtitle}</div>` : ''}
    </div>
  `;
}

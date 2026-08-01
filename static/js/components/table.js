/**
 * Table UI Component
 */

function createTable(headers, rows) {
  if (!rows || rows.length === 0) {
    return `<div style="text-align: center; padding: 48px; color: var(--text-muted);">
      <p>No data available</p>
    </div>`;
  }

  const thead = `
    <thead>
      <tr style="border-bottom: 1px solid var(--color-light-gray); text-align: left;">
        ${headers.map(h => `<th style="padding: 12px 16px; font-weight: 500; color: var(--text-muted); font-size: 13px; text-transform: uppercase;">${h}</th>`).join('')}
      </tr>
    </thead>
  `;

  const tbody = `
    <tbody>
      ${rows.map(row => `
        <tr style="border-bottom: 1px solid var(--color-light-gray); transition: background-color 0.15s;">
          ${row.map(cell => `<td style="padding: 16px;">${cell}</td>`).join('')}
        </tr>
      `).join('')}
    </tbody>
  `;

  return `
    <div style="width: 100%; overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse;">
        ${thead}
        ${tbody}
      </table>
    </div>
  `;
}

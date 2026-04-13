/**
 * 张力仪表盘组件
 */
class TensionMeter {
  constructor(container) {
    this.container = container;
    this.data = { conflict: 0.5, suspense: 0.5, emotion: 0.5, rhythm: 0.5, overall: 0.5 };
    this.render();
  }

  update(data) {
    this.data = data;
    this.render();
  }

  render() {
    const items = [
      { key: 'conflict', label: '冲突', color: '#e94560' },
      { key: 'suspense', label: '悬念', color: '#fbbf24' },
      { key: 'emotion', label: '情感', color: '#4ade80' },
      { key: 'rhythm', label: '节奏', color: '#60a5fa' }
    ];

    const html = `
      <div class="card-title">张力仪表盘</div>
      <div class="tension-meter">
        ${items.map(item => `
          <div class="tension-item">
            <div class="tension-label">${item.label}</div>
            <div class="tension-bar">
              <div class="tension-fill" style="width:${this.data[item.key]*100}%;background:${item.color}"></div>
            </div>
            <div style="font-size:11px;margin-top:2px">${Math.round(this.data[item.key]*100)}%</div>
          </div>
        `).join('')}
      </div>
      <div style="margin-top:12px;text-align:center">
        <span style="font-size:12px;color:var(--text-secondary)">综合张力</span>
        <div style="font-size:24px;font-weight:bold;color:var(--accent)">${Math.round(this.data.overall*100)}</div>
      </div>
    `;
    this.container.innerHTML = html;
  }
}

window.TensionMeter = TensionMeter;

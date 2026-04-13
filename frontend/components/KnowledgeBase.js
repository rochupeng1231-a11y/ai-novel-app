/**
 * 知识库面板组件
 */
class KnowledgeBase {
  constructor(container) {
    this.container = container;
    this.foreshadows = [];
    this.tabs = 'foreshadow';
  }

  update(foreshadows) {
    this.foreshadows = foreshadows;
    this.render();
  }

  render() {
    const tabs = ['伏笔', '战力', '时间线'];
    const html = `
      <div class="card-title">知识库</div>
      <div style="display:flex;gap:4px;margin-bottom:12px">
        ${tabs.map((tab, i) => `
          <button class="btn btn-secondary" style="flex:1;padding:4px;font-size:11px"
                  onclick="app.knowledgeBase.switchTab('${tab}')">
            ${tab}
          </button>
        `).join('')}
      </div>
      <div id="knowledge-content">
        ${this.renderForeshadows()}
      </div>
    `;
    this.container.innerHTML = html;
  }

  switchTab(tab) {
    this.tabs = tab;
    document.getElementById('knowledge-content').innerHTML = this.renderForeshadows();
  }

  renderForeshadows() {
    const statusMap = { planted: '已埋', triggered: '已触发', resolved: '已回收' };
    const colorMap = { planted: '#fbbf24', triggered: '#e94560', resolved: '#4ade80' };

    if (this.foreshadows.length === 0) {
      return '<div style="color:var(--text-secondary);font-size:13px;text-align:center">暂无伏笔</div>';
    }

    return this.foreshadows.map(f => `
      <div style="margin-bottom:8px;padding:8px;background:var(--bg-primary);border-radius:4px">
        <div style="display:flex;justify-content:space-between">
          <span style="font-weight:500">${f.keyword}</span>
          <span style="font-size:11px;color:${colorMap[f.status]}">${statusMap[f.status]}</span>
        </div>
        <div style="font-size:12px;color:var(--text-secondary)">${f.description || ''}</div>
      </div>
    `).join('');
  }
}

window.KnowledgeBase = KnowledgeBase;

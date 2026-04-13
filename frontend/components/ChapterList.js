/**
 * 章节列表组件
 */
class ChapterList {
  constructor(container) {
    this.container = container;
    this.chapters = [];
    this.activeId = null;
    this.onSelect = null;
  }

  setOnSelect(callback) {
    this.onSelect = callback;
  }

  update(chapters) {
    this.chapters = chapters;
    this.render();
  }

  render() {
    const html = `
      <div class="card-title">章节</div>
      <button class="btn btn-primary" style="width:100%;margin-bottom:12px" onclick="app.addChapter()">
        + 新建章节
      </button>
      <div>
        ${this.chapters.map(ch => `
          <div class="list-item ${ch.id === this.activeId ? 'active' : ''}" 
               onclick="app.selectChapter('${ch.id}')">
            <div style="display:flex;justify-content:space-between">
              <span>第${ch.number}章</span>
              <span style="font-size:11px;color:${this.getStatusColor(ch.status)}">${ch.status}</span>
            </div>
            <div style="font-size:12px;color:var(--text-secondary)">${ch.title || '未命名'}</div>
            <div style="font-size:11px;color:var(--text-secondary)">${ch.wordCount}字</div>
          </div>
        `).join('')}
      </div>
    `;
    this.container.innerHTML = html;
  }

  getStatusColor(status) {
    const colors = { draft: '#a0a0a0', writing: '#fbbf24', completed: '#4ade80' };
    return colors[status] || '#a0a0a0';
  }
}

window.ChapterList = ChapterList;

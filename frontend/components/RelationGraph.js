/**
 * 关系图谱组件
 */
class RelationGraph {
  constructor(container) {
    this.container = container;
    this.characters = [];
    this.relations = [];
  }

  update(characters, relations) {
    this.characters = characters;
    this.relations = relations;
    this.render();
  }

  render() {
    if (this.characters.length === 0) {
      this.container.innerHTML = `
        <div class="card-title">关系图谱</div>
        <div style="color:var(--text-secondary);font-size:13px;text-align:center;padding:20px">
          暂无角色<br>请先创建角色
        </div>
      `;
      return;
    }

    const width = this.container.clientWidth || 250;
    const height = 200;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 70;

    // 计算角色位置
    const positions = this.characters.map((char, i) => {
      const angle = (2 * Math.PI * i) / this.characters.length - Math.PI / 2;
      return {
        ...char,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    // SVG连线
    const lines = this.relations.map(rel => {
      const a = positions.find(p => p.id === rel.characterA);
      const b = positions.find(p => p.id === rel.characterB);
      if (!a || !b) return '';
      return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" 
                    stroke="var(--border)" stroke-width="1"/>`;
    }).join('');

    // 节点
    const nodes = positions.map(p => `
      <g transform="translate(${p.x},${p.y})">
        <circle r="20" fill="var(--bg-tertiary)" stroke="var(--accent)" stroke-width="2"/>
        <text text-anchor="middle" dy="4" fill="var(--text-primary)" font-size="10">
          ${p.name.substring(0, 2)}
        </text>
      </g>
    `).join('');

    const html = `
      <div class="card-title">关系图谱</div>
      <svg width="${width}" height="${height}">
        ${lines}
        ${nodes}
      </svg>
      <div style="margin-top:8px">
        ${this.relations.map(r => `
          <div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px">
            ${this.getCharName(r.characterA)} —${r.relationType}— ${this.getCharName(r.characterB)}
          </div>
        `).join('')}
      </div>
    `;
    this.container.innerHTML = html;
  }

  getCharName(id) {
    const char = this.characters.find(c => c.id === id);
    return char ? char.name : '?';
  }
}

window.RelationGraph = RelationGraph;

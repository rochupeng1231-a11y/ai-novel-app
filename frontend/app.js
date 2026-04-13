/**
 * AI 写小说 - 主应用（模块编排层）
 * 各模块：modules/api.js, modules/state.js, modules/project.js, modules/outline.js, modules/writing.js
 */

// 静态数据（类型/元素选项）
const NOVEL_TYPES = [
  { id: 'urban', name: '都市言情', icon: '🏙️', desc: '现代都市背景的爱情故事' },
  { id: 'fantasy', name: '玄幻修仙', icon: '🗡️', desc: '仙侠世界的修炼成神之路' },
  { id: 'suspense', name: '悬疑推理', icon: '🔍', desc: '层层迷雾中的真相追寻' },
  { id: 'scifi', name: '科幻未来', icon: '🚀', desc: '未来世界的星际探索' },
  { id: 'wuxia', name: '武侠江湖', icon: '⚔️', desc: '刀光剑影的江湖恩怨' },
  { id: 'campus', name: '校园青春', icon: '📚', desc: '青春校园的成长故事' }
];

const CORE_ELEMENTS = ['逆袭崛起', '命中注定', '复仇之路', '成长蜕变', '商战博弈', '穿越时空', '异能觉醒', '甜宠爱情', '虐恋情深', '热血兄弟'];

// 组件实例
let chapterList, relationGraph, knowledgeBase;

// ============ 初始化 ============
async function init() {
  chapterList = new ChapterList(document.getElementById('chapter-list'));
  relationGraph = new RelationGraph(document.getElementById('relation-graph'));
  knowledgeBase = new KnowledgeBase(document.getElementById('knowledge-base'));
  chapterList.setOnSelect(id => projectModule.selectChapter(id));
  await projectModule.loadProjects();
  updateUI();
}

// ============ UI 更新 ============
function updateUI() {
  const steps = ['project', 'outline', 'chapters', 'writing'];
  steps.forEach(step => {
    const el = document.getElementById(`step-${step}`);
    if (el) el.classList.toggle('active', step === stateManager.state.step);
  });

  const stepMap = { 'project': 1, 'outline': 2, 'chapters': 3, 'writing': 4 };
  const activeIdx = stepMap[stateManager.state.step] || 1;
  for (let i = 1; i <= 4; i++) {
    const ind = document.getElementById(`step-ind-${i}`);
    if (ind) ind.classList.toggle('active', i === activeIdx);
  }

  if (stateManager.state.step === 'project') {
    renderProjectList();
  }

  if (stateManager.state.step === 'outline') {
    outlineModule.renderOutlineSelect();
    outlineModule.showOutlineSelect();
  }

  if (stateManager.state.step === 'chapters' || stateManager.state.step === 'writing') {
    // 更新章节列表
    if (chapterList) {
      chapterList.update(stateManager.state.chapters.map(c => ({
        id: c.id, number: c.number, title: c.title || `第${c.number}章`,
        status: c.status, wordCount: c.word_count || 0
      })));
    }
    // 更新关系图谱
    relationGraph.update(stateManager.state.characters, stateManager.state.relations.map(r => ({
      id: r.id, characterA: r.character_a_id, characterB: r.character_b_id, relationType: r.relation_type
    })));
    // 更新知识库
    knowledgeBase.update(stateManager.state.foreshadows);

    // 更新大纲预览
    const outlinePreviewEl = document.getElementById('outline-preview');
    if (outlinePreviewEl) {
      const outline = stateManager.state.currentOutline;
      if (outline && outline.content) {
        outlinePreviewEl.textContent = outline.content;
      } else {
        outlinePreviewEl.textContent = '请在左侧选择一个章节开始写作';
      }
    }

    const totalWords = stateManager.state.chapters.reduce((sum, c) => sum + (c.word_count || 0), 0);
    ['stat-chapters', 'stat-chapters-w'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = stateManager.state.chapters.length;
    });
    ['stat-words', 'stat-words-w'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = totalWords.toLocaleString();
    });

    if (stateManager.state.currentChapter) {
      const nameEl = document.getElementById('current-chapter-name');
      if (nameEl) nameEl.textContent = `第${stateManager.state.currentChapter.number}章 ${stateManager.state.currentChapter.title || ''}`;
    }
  }

  if (stateManager.state.currentProject) {
    const nameEl = document.getElementById('current-project-name');
    if (nameEl) nameEl.textContent = stateManager.state.currentProject.name;
    const projectName = document.getElementById('project-name');
    if (projectName) projectName.textContent = stateManager.state.currentProject.name;
  }
}

// ============ 项目列表渲染 ============
function renderProjectList() {
  const container = document.getElementById('project-list-container');
  if (!container) return;

  if (stateManager.state.projects.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:var(--text-secondary);padding:40px">暂无项目，请创建新项目</div>';
    return;
  }

  container.innerHTML = stateManager.state.projects.map(p => `
    <div class="project-card" onclick="app.openProject('${p.id}')">
      <div class="project-info">
        <div class="project-title">${p.name}</div>
        <div class="project-meta">目标: ${p.target_word_count || 300000}字</div>
      </div>
      <button class="btn-delete" onclick="event.stopPropagation();app.deleteProject('${p.id}')">🗑️</button>
    </div>
  `).join('');
}

// 设置大纲进度条（供 outline 模块调用）
function setProgressInline(pct, text) {
  const progressEl = document.getElementById('outline-progress');
  const barEl = document.getElementById('outline-progress-bar');
  if (progressEl) progressEl.textContent = text;
  if (barEl) barEl.style.width = pct + '%';
}

// ============ 暴露给 HTML 的 app 对象 ============
window.app = {
  init,

  // 项目
  createProject: projectModule.createProject,
  openProject: projectModule.openProject,
  deleteProject: projectModule.deleteProject,
  backToProject: outlineModule.backToProject,

  // 大纲
  selectNovelType: outlineModule.selectNovelType,
  toggleElement: outlineModule.toggleElement,
  generateOutline: outlineModule.generateOutline,
  regenerateOutline: outlineModule.regenerateOutline,

  // 章节
  addChapter: projectModule.addChapter,
  selectChapter: projectModule.selectChapter,
  backToChapters: projectModule.backToChapters,

  // 写作
  startWriting: writingModule.startWriting,
  stopWriting: writingModule.stopWriting,
  saveChapter: writingModule.saveChapter,
  onEditorInput: writingModule.onEditorInput,
  updateWordCount: writingModule.updateWordCount
};

document.addEventListener('DOMContentLoaded', init);
init();

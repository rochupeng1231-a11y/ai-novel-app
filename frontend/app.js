/**
 * AI 写小说 - 主应用
 */
const API_BASE = '/api';

const state = {
  projects: [],
  currentProject: null,
  chapters: [],
  characters: [],
  relations: [],
  foreshadows: [],
  currentChapter: null,
  currentOutline: null,
  isWriting: false,
  step: 'projects'
};

let chapterList, relationGraph, knowledgeBase;

const NOVEL_TYPES = [
  { id: 'urban', name: '都市言情', icon: '🏙️', desc: '现代都市背景的爱情故事' },
  { id: 'fantasy', name: '玄幻修仙', icon: '🗡️', desc: '仙侠世界的修炼成神之路' },
  { id: 'suspense', name: '悬疑推理', icon: '🔍', desc: '层层迷雾中的真相追寻' },
  { id: 'scifi', name: '科幻未来', icon: '🚀', desc: '未来世界的星际探索' },
  { id: 'wuxia', name: '武侠江湖', icon: '⚔️', desc: '刀光剑影的江湖恩怨' },
  { id: 'campus', name: '校园青春', icon: '📚', desc: '青春校园的成长故事' }
];

const CORE_ELEMENTS = ['逆袭崛起', '命中注定', '复仇之路', '成长蜕变', '商战博弈', '穿越时空', '异能觉醒', '甜宠爱情', '虐恋情深', '热血兄弟'];

let selectedType = null;
let selectedElements = [];

async function init() {
  chapterList = new ChapterList(document.getElementById('chapter-list'));
  relationGraph = new RelationGraph(document.getElementById('relation-graph'));
  knowledgeBase = new KnowledgeBase(document.getElementById('knowledge-base'));
  chapterList.setOnSelect(id => selectChapter(id));
  await loadProjects();
  updateUI();
}

async function loadProjects() {
  try {
    const res = await fetch(`${API_BASE}/db/projects`);
    state.projects = await res.json();
  } catch (e) {
    state.projects = [];
  }
}

// ============ 项目列表 ============
function showProjectList() {
  state.step = 'projects';
  updateUI();
}

async function createProject() {
  const name = document.getElementById('project-name-input')?.value || '新小说';
  try {
    const res = await fetch(`${API_BASE}/db/projects`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, description: '', target_word_count: 300000})
    });
    const newProject = await res.json();
    state.projects.push(newProject);
    state.currentProject = newProject;
    state.step = 'outline';
    updateUI();
  } catch (e) {
    alert('创建失败: ' + e.message);
  }
}

async function openProject(projectId) {
  state.currentProject = state.projects.find(p => p.id === projectId);
  if (state.currentProject) {
    await loadProjectData();
    state.step = 'chapters';
    updateUI();
  }
}

async function deleteProject(projectId) {
  if (!confirm('确定删除此项目？')) return;
  try {
    await fetch(`${API_BASE}/db/projects/${projectId}`, { method: 'DELETE' });
    state.projects = state.projects.filter(p => p.id !== projectId);
    if (state.currentProject?.id === projectId) {
      state.currentProject = null;
      state.chapters = [];
    }
    updateUI();
  } catch (e) {
    alert('删除失败');
  }
}

// ============ 选择类型 ============
function selectNovelType(typeId) {
  selectedType = NOVEL_TYPES.find(t => t.id === typeId);
  document.querySelectorAll('.type-card').forEach(card => card.classList.remove('selected'));
  event.target.closest('.type-card').classList.add('selected');
}

function toggleElement(element) {
  const idx = selectedElements.indexOf(element);
  if (idx > -1) selectedElements.splice(idx, 1);
  else if (selectedElements.length < 3) selectedElements.push(element);
  else { alert('最多3个'); return; }
  updateElementUI();
}

function updateElementUI() {
  document.querySelectorAll('.element-tag').forEach(tag => {
    if (selectedElements.includes(tag.textContent.trim())) tag.classList.add('selected');
    else tag.classList.remove('selected');
  });
}

// ============ 生成大纲 ============
async function generateOutline() {
  if (!selectedType) { alert('请选类型'); return; }
  state.isWriting = true;
  updateUI();
  const elements = selectedElements.length > 0 ? selectedElements.join('、') : '热血激情';
  try {
    const response = await fetch(`${API_BASE}/writing`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({chapter_id: 'outline', instruction: '大纲', context: `请为【${selectedType.name}】类型小说生成大纲。核心元素：${elements}。要求：1.故事主线 2.主要人物(3-5个) 3.章节结构(10-15章) 4.每章简要描述 5.重要情节点`})
    });
    const result = await response.json();
    state.currentOutline = {type: selectedType.name, content: result.content, created_at: new Date().toISOString()};
    await createChaptersFromOutline(result.content);
    state.step = 'chapters';
  } catch (e) { alert('生成失败: ' + e.message); }
  finally { state.isWriting = false; updateUI(); }
}

async function createChaptersFromOutline(outline) {
  const lines = outline.split('\n');
  let num = 0;
  for (const line of lines) {
    if (/^第[一二三四五六七八九十百\d]+章/.test(line.trim())) {
      num++;
      const title = line.replace(/^第[一二三四五六七八九十百\d]+章[：:\s]*/, '').trim() || `第${num}章`;
      await fetch(`${API_BASE}/db/chapters`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({project_id: state.currentProject.id, number: num, title})
      });
    }
  }
  await loadProjectData();
}

function regenerateOutline() {
  selectedType = null;
  selectedElements = [];
  state.step = 'outline';
  updateUI();
}

// ============ 章节 ============
async function addChapter() {
  const num = state.chapters.length + 1;
  await fetch(`${API_BASE}/db/chapters`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({project_id: state.currentProject.id, number: num, title: `第${num}章`})
  });
  await loadProjectData();
  updateUI();
}

async function selectChapter(id) {
  const chapter = state.chapters.find(c => c.id === id);
  if (!chapter) return;
  state.currentChapter = chapter;
  chapterList.activeId = id;
  chapterList.render();
  state.step = 'writing';
  const editor = document.getElementById('editor');
  if (editor) editor.value = chapter.content || '';
  updateWordCount();
  updateUI();
}

function backToChapters() {
  state.step = 'chapters';
  state.currentChapter = null;
  updateUI();
}

// ============ 写作 ============
async function startWriting(instruction) {
  if (state.isWriting) return;
  const content = document.getElementById('editor')?.value || '';
  state.isWriting = true;
  state.currentInstruction = instruction;
  updateWritingButtons();
  updateUI();
  try {
    const response = await fetch(`${API_BASE}/writing`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({chapter_id: state.currentChapter?.id || 'writing', instruction, context: content})
    });
    const result = await response.json();
    const editor = document.getElementById('editor');
    if (editor && result.content) {
      editor.value = content + '\n\n' + result.content;
      updateWordCount();
    }
  } catch (e) { console.error('失败:', e); }
  finally { state.isWriting = false; updateWritingButtons(); updateUI(); }
}

function stopWriting() { state.isWriting = false; updateWritingButtons(); updateUI(); }

function updateWritingButtons() {
  const iDiv = document.getElementById('writing-instructions');
  const cDiv = document.getElementById('writing-controls');
  if (state.isWriting) {
    if (iDiv) iDiv.style.display = 'none';
    if (cDiv) cDiv.style.display = 'flex';
  } else {
    if (iDiv) iDiv.style.display = 'flex';
    if (cDiv) cDiv.style.display = 'none';
  }
}

async function saveChapter() {
  if (!state.currentChapter) return;
  const content = document.getElementById('editor')?.value || '';
  try {
    await fetch(`${API_BASE}/db/chapters/${state.currentChapter.id}/versions`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({chapter_id: state.currentChapter.id, content, change_summary: '保存'})
    });
    await fetch(`${API_BASE}/db/chapters/${state.currentChapter.id}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({content, status: content.length > 100 ? 'writing' : 'draft'})
    });
    await loadProjectData();
    alert('保存成功');
  } catch (e) { alert('保存失败: ' + e.message); }
}

async function loadProjectData() {
  if (!state.currentProject) return;
  const pid = state.currentProject.id;
  try {
    const [cr, chr, rr, fr] = await Promise.all([
      fetch(`${API_BASE}/db/chapters/project/${pid}`),
      fetch(`${API_BASE}/db/characters/project/${pid}`),
      fetch(`${API_BASE}/db/relations/project/${pid}`),
      fetch(`${API_BASE}/db/foreshadows/project/${pid}`)
    ]);
    state.chapters = await cr.json();
    state.characters = await chr.json();
    state.relations = await rr.json();
    state.foreshadows = await fr.json();
  } catch (e) { console.error('加载失败:', e); }
}

// ============ 辅助 ============
function updateWordCount() {
  const content = document.getElementById('editor')?.value || '';
  const count = content.replace(/\s/g, '').length;
  const wc = document.getElementById('word-count');
  if (wc) wc.textContent = count;
}

let tensionTimer = null;
function onEditorInput() {
  if (tensionTimer) clearTimeout(tensionTimer);
  tensionTimer = setTimeout(() => {
    analyzeRealtimeTension();
    updateWordCount();
  }, 500);
}

function analyzeRealtimeTension() {
  const content = document.getElementById('editor')?.value || '';
  if (!content || content.length < 50) return;
  const scores = localTensionAnalyze(content);
  updateRealtimeTensionDisplay(scores);
}

function localTensionAnalyze(text) {
  const ck = ['怒', '吼', '骂', '吵', '争', '夺', '砸', '冷笑', '对峙', '凭什么', '争吵', '打架', '矛盾', '冲突'];
  const sk = ['突然', '忽然', '猛地', '难道', '究竟', '到底', '就在这时', '没想到', '然而', '但是', '……'];
  const ek = ['愤怒', '悲伤', '恐惧', '惊讶', '心痛', '激动', '绝望', '爱', '恨', '不舍', '害怕', '颤抖', '流泪', '心想'];
  const cs = Math.min(ck.filter(k => text.includes(k)).length / 3, 1);
  const ss = Math.min(sk.filter(k => text.includes(k)).length / 3, 1);
  const es = Math.min(ek.filter(k => text.includes(k)).length / 3, 1);
  const sentences = text.split(/[。！？]/).filter(s => s.trim().length > 0);
  const shortSentences = sentences.filter(s => s.length < 20);
  const rs = sentences.length > 0 ? Math.min(shortSentences.length / sentences.length, 1) : 0.5;
  return {conflict: cs, suspense: ss, emotion: es, rhythm: rs, overall: (cs + ss + es + rs) / 4};
}

function updateRealtimeTensionDisplay(scores) {
  const p = v => Math.round(v * 100);
  ['conflict', 'suspense', 'emotion', 'rhythm'].forEach(dim => {
    const el = document.getElementById(`rt-${dim}`);
    if (el) el.textContent = p(scores[dim]);
  });
  const overall = document.getElementById('rt-overall');
  if (overall) overall.textContent = p(scores.overall);
}

// ============ UI更新 ============
function updateUI() {
  const steps = ['projects', 'outline', 'chapters', 'writing'];
  const currentIdx = steps.indexOf(state.step);
  
  steps.forEach(step => {
    const el = document.getElementById(`step-${step}`);
    if (el) el.style.display = step === state.step ? 'block' : 'none';
  });
  
  if (state.step === 'projects') renderProjectList();
  
  if (state.step === 'chapters' || state.step === 'writing') {
    if (chapterList) {
      chapterList.update(state.chapters.map(c => ({
        id: c.id, number: c.number, title: c.title || `第${c.number}章`,
        status: c.status, wordCount: c.word_count || 0
      })));
    }
    relationGraph.update(state.characters, state.relations.map(r => ({
      id: r.id, characterA: r.character_a_id, characterB: r.character_b_id, relationType: r.relation_type
    })));
    knowledgeBase.update(state.foreshadows);
    
    const totalWords = state.chapters.reduce((sum, c) => sum + (c.word_count || 0), 0);
    ['stat-chapters', 'stat-chapters-w'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = state.chapters.length;
    });
    ['stat-words', 'stat-words-w'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = totalWords.toLocaleString();
    });
    
    if (state.currentChapter) {
      const nameEl = document.getElementById('current-chapter-name');
      if (nameEl) nameEl.textContent = `第${state.currentChapter.number}章 ${state.currentChapter.title || ''}`;
    }
  }
  
  if (state.currentProject) {
    const nameEl = document.getElementById('current-project-name');
    if (nameEl) nameEl.textContent = state.currentProject.name;
  }
}

function renderProjectList() {
  const container = document.getElementById('project-list-container');
  if (!container) return;
  
  let html = state.projects.map(p => `
    <div class="project-card" onclick="app.openProject('${p.id}')">
      <div class="project-info">
        <div class="project-title">${p.name}</div>
        <div class="project-meta">目标: ${p.target_word_count || 300000}字</div>
      </div>
      <button class="btn-delete" onclick="event.stopPropagation();app.deleteProject('${p.id}')">🗑️</button>
    </div>
  `).join('');
  
  html += `<div class="add-project-card" onclick="app.createProject()">
    <div class="add-icon">+</div>
    <div class="add-text">新建项目</div>
  </div>`;
  
  container.innerHTML = html;
}

window.app = {
  init, showProjectList, createProject, openProject, deleteProject,
  selectNovelType, toggleElement, generateOutline, regenerateOutline,
  addChapter, selectChapter, backToChapters,
  startWriting, stopWriting, saveChapter,
  onEditorInput, updateWordCount
};

document.addEventListener('DOMContentLoaded', init);

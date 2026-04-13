/**
 * 项目与章节管理模块
 */

// ============ 项目列表 ============
async function loadProjects() {
  try {
    stateManager.state.projects = await api.getProjects();
  } catch (e) {
    stateManager.state.projects = [];
  }
}

async function createProject() {
  const name = document.getElementById('project-name-input')?.value || '新小说';
  try {
    const newProject = await api.createProject(name);
    stateManager.state.projects.push(newProject);
    stateManager.setCurrentProject(newProject);
    stateManager.setStep('outline');
    updateUI();
  } catch (e) {
    alert('创建失败: ' + e.message);
  }
}

async function openProject(projectId) {
  const project = stateManager.state.projects.find(p => p.id === projectId);
  if (project) {
    stateManager.setCurrentProject(project);
    await loadProjectData();
    stateManager.setStep('chapters');
    updateUI();
  }
}

async function deleteProject(projectId) {
  if (!confirm('确定删除此项目？')) return;
  try {
    await api.deleteProject(projectId);
    stateManager.state.projects = stateManager.state.projects.filter(p => p.id !== projectId);
    if (stateManager.state.currentProject?.id === projectId) {
      stateManager.resetProjectState();
    }
    updateUI();
  } catch (e) {
    alert('删除失败');
  }
}

// ============ 章节 ============
async function addChapter() {
  const num = stateManager.state.chapters.length + 1;
  try {
    await api.createChapter(stateManager.state.currentProject.id, num, `第${num}章`);
    await loadProjectData();
    updateUI();
  } catch (e) { alert('创建章节失败'); }
}

async function selectChapter(id) {
  const chapter = stateManager.state.chapters.find(c => c.id === id);
  if (!chapter) return;
  stateManager.setCurrentChapter(chapter);
  chapterList.activeId = id;
  chapterList.render();
  stateManager.setStep('writing');
  const editor = document.getElementById('editor');
  if (editor) editor.value = chapter.content || '';
  writingModule.updateWordCount();
  writingModule.updateWritingButtons(); // 更新按钮显示状态
  updateUI();
}

function backToChapters() {
  stateManager.setStep('chapters');
  stateManager.setCurrentChapter(null);
  updateUI();
}

async function loadProjectData() {
  if (!stateManager.state.currentProject) return;
  const pid = stateManager.state.currentProject.id;
  try {
    const [cr, chr, rr, fr] = await Promise.all([
      fetch(`${API_BASE}/db/chapters/project/${pid}`),
      fetch(`${API_BASE}/db/characters/project/${pid}`),
      fetch(`${API_BASE}/db/relations/project/${pid}`),
      fetch(`${API_BASE}/db/foreshadows/project/${pid}`)
    ]);
    const chapters = await cr.json();
    const characters = await chr.json();
    const relations = await rr.json();
    const foreshadows = await fr.json();
    console.log('[加载] 章节:', chapters.length, '角色:', characters.length, '关系:', relations.length, '伏笔:', foreshadows.length);
    stateManager.setChapters(chapters);
    stateManager.setCharacters(characters);
    stateManager.setRelations(relations);
    stateManager.setForeshadows(foreshadows);
  } catch (e) { console.error('加载失败:', e); }
}

window.projectModule = {
  loadProjects, createProject, openProject, deleteProject,
  addChapter, selectChapter, backToChapters, loadProjectData
};
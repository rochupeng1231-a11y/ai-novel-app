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
  const steps = ['project', 'outline', 'chapters', 'writing', 'batch-review'];
  steps.forEach(step => {
    const el = document.getElementById(`step-${step}`);
    if (el) el.classList.toggle('active', step === stateManager.state.step);
  });

  const stepMap = { 'project': 1, 'outline': 2, 'chapters': 3, 'writing': 4, 'batch-review': 5 };
  const activeIdx = stepMap[stateManager.state.step] || 1;
  for (let i = 1; i <= 5; i++) {
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

    // 更新批量写作章节选择器
    updateBatchChapterSelector();
  }

  if (stateManager.state.currentProject) {
    const nameEl = document.getElementById('current-project-name');
    if (nameEl) nameEl.textContent = stateManager.state.currentProject.name;
    const projectName = document.getElementById('project-name');
    if (projectName) projectName.textContent = stateManager.state.currentProject.name;
  }
}

// 批量章节选择
const selectedBatchChapters = new Set();

function updateBatchChapterSelector() {
  const container = document.getElementById('batch-chapter-selector');
  if (!container) return;

  const chapters = stateManager.state.chapters || [];
  if (chapters.length === 0) {
    container.innerHTML = '<div style="color:#888;font-size:11px">暂无章节</div>';
    return;
  }

  container.innerHTML = chapters.map(ch => `
    <label style="display:flex;align-items:center;gap:4px;padding:2px 0;cursor:pointer">
      <input type="checkbox" value="${ch.id}" ${selectedBatchChapters.has(ch.id) ? 'checked' : ''}
        onchange="app.toggleBatchChapter('${ch.id}')">
      <span>第${ch.number}章</span>
    </label>
  `).join('');
}

function toggleBatchChapter(chapterId) {
  if (selectedBatchChapters.has(chapterId)) {
    selectedBatchChapters.delete(chapterId);
  } else {
    selectedBatchChapters.add(chapterId);
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
  updateWordCount: writingModule.updateWordCount,

  // BVSR/SWAG
  addSwagAnchor: function(eventText) {
    if (!eventText) {
      const input = document.getElementById('swag-anchor-input');
      eventText = input?.value?.trim();
    }
    writingModule.addSwagAnchor(eventText);
    const input = document.getElementById('swag-anchor-input');
    if (input) input.value = '';
  },
  removeSwagAnchor: writingModule.removeSwagAnchor,
  getSwagAnchors: writingModule.getSwagAnchors,

  // Continuity 刷新
  refreshContinuity: async function() {
    if (!stateManager.state.currentProject) return;
    try {
      const summary = await api.getProjectSummary(stateManager.state.currentProject.id);
      const timeline = await api.getProjectTimeline(stateManager.state.currentProject.id, 20);
      const charStates = await api.getCharacterStates(stateManager.state.currentProject.id);
      // 可以在 UI 上显示这些数据，比如在写作面板显示连贯性摘要
      console.log('[Continuity] 刷新摘要:', summary);
      console.log('[Continuity] 时间线事件:', timeline.events?.length);
      console.log('[Continuity] 角色状态:', charStates.states?.length);
    } catch (e) {
      console.error('[Continuity] 刷新失败:', e);
    }
  },

  // 批量写作
  toggleBatchChapter,
  startBatchWriting: async function() {
    if (selectedBatchChapters.size === 0) {
      alert('请先选择要写的章节');
      return;
    }

    const projectId = stateManager.state.currentProject?.id;
    if (!projectId) {
      alert('请先打开项目');
      return;
    }

    const chapterIds = Array.from(selectedBatchChapters);
    console.log('[批量写作] 开始，章节:', chapterIds);

    try {
      // 启动批量写作
      const result = await api.batchWriteStart(projectId, chapterIds, '续写');
      console.log('[批量写作] 启动成功:', result);

      // 保存批量写作会话信息
      stateManager.state.batchSession = {
        batchId: result.batch_id,
        totalChapters: result.total_chapters,
        currentIndex: 0,
        chapters: []
      };

      // 跳转到审核页面
      stateManager.setStep('batch-review');
      updateUI();

      // 开始第一章节的写作
      await writeNextBatchChapter();

    } catch (e) {
      console.error('[批量写作] 启动失败:', e);
      alert('批量写作启动失败: ' + e.message);
    }
  }
};

// 批量写作会话状态
let batchSession = null;
// 当前生成的内容
let currentBatchContent = '';
// 当前章节ID
let currentBatchChapterId = null;

async function writeNextBatchChapter() {
  const session = stateManager.state.batchSession;
  if (!session) return;

  const editor = document.getElementById('batch-editor');
  if (editor) editor.value = '';
  currentBatchContent = '';

  try {
    // 1. 获取下一章节信息
    const nextInfo = await api.batchWriteGetNextChapter(session.batchId);
    if (nextInfo.status === 'completed') {
      alert('批量写作完成！');
      stateManager.state.batchSession = null;
      stateManager.setStep('chapters');
      updateUI();
      await projectModule.loadProjectData();
      return;
    }

    console.log('[批量写作] 开始写第' + nextInfo.chapter_number + '章...');
    currentBatchChapterId = nextInfo.chapter_id;

    const statusEl = document.getElementById('batch-status');
    if (statusEl) statusEl.textContent = '写作中...';

    // 更新UI
    document.getElementById('batch-chapter-name').textContent = '第' + nextInfo.chapter_number + '章: ' + nextInfo.chapter_title;
    document.getElementById('batch-current').textContent = session.currentIndex + 1;

    // 2. 构建上下文（包含上一章内容用于衔接）
    let context = '';
    if (nextInfo.use_previous_content) {
      context = '\n【上一章情节承接】\n' + nextInfo.use_previous_content;
      console.log('[批量写作] 使用第' + nextInfo.use_previous_chapter_num + '章作为上文');
    }

    // 3. 调用单章节写作API
    await api.writeStream(currentBatchChapterId, '续写', context, {
      onChunk(content) {
        if (editor) editor.value += content;
        currentBatchContent += content;
      },
      onDone(evt) {
        console.log('[批量写作] 第' + nextInfo.chapter_number + '章完成');
        updateBatchReviewUI();

        if (editor && evt.content) {
          editor.value = evt.content;
          currentBatchContent = evt.content;
        }

        // 4. 标记章节完成
        api.batchWriteCompleteChapter(session.batchId, currentBatchChapterId, currentBatchContent, evt.tension_score || 0.5)
          .then(() => updateBatchReviewDimensions(currentBatchContent, evt.tension_score || 0.5))
          .catch(e => console.error('[批量写作] 标记完成失败:', e));
      },
      onError(msg) {
        console.error('[批量写作] 错误:', msg);
        alert('写作错误: ' + msg);
      }
    });
  } catch (e) {
    console.error('[批量写作] 获取下一章失败:', e);
  }
}

function updateBatchReviewUI() {
  const session = stateManager.state.batchSession;
  if (!session) return;

  const currentEl = document.getElementById('batch-current');
  const totalEl = document.getElementById('batch-total');
  const statusEl = document.getElementById('batch-status');

  if (currentEl) currentEl.textContent = session.currentIndex + 1;
  if (totalEl) totalEl.textContent = session.totalChapters;
  if (statusEl) statusEl.textContent = '待审核';
}

window.app.batchReview = async function(action) {
  const session = stateManager.state.batchSession;
  if (!session) return;

  const content = document.getElementById('batch-editor')?.value || currentBatchContent;

  try {
    console.log('[审核] 操作:', action);
    const result = await api.batchWriteReview(session.batchId, action, content);
    console.log('[审核] 结果:', result);

    if (result.status === 'completed') {
      alert('批量写作完成！');
      stateManager.state.batchSession = null;
      stateManager.setStep('chapters');
      updateUI();
      await projectModule.loadProjectData();
    } else {
      // 移动到下一章
      session.currentIndex = result.current_index;
      currentBatchContent = '';
      const editor = document.getElementById('batch-editor');
      if (editor) editor.value = '';
      updateBatchReviewUI();
      // 重置评分
      currentRating = 0;
      document.getElementById('batch-rating').textContent = '未评分';
      // 开始写下一章
      await writeNextBatchChapter();
    }
  } catch (e) {
    console.error('[审核] 操作失败:', e);
    alert('审核操作失败: ' + e.message);
  }
};

// 章节评分
let currentRating = 0;

window.app.rateChapter = function(rating) {
  currentRating = rating;
  const stars = '★'.repeat(rating) + '☆'.repeat(5 - rating);
  document.getElementById('batch-rating').textContent = stars;
  console.log('[评分] 章节评分:', rating, '星');
};

// 更新审核维度显示
async function updateBatchReviewDimensions(content, tensionScore) {
  const session = stateManager.state.batchSession;
  const projectId = stateManager.state.currentProject?.id;

  // 更新字数
  const words = content.replace(/\s/g, '').length;
  document.getElementById('batch-chapter-words').textContent = words;

  // 更新张力分数
  document.getElementById('batch-chapter-tension').textContent = Math.round(tensionScore * 100);

  // 更新张力维度（从本地分析）
  const tension = localTensionAnalyze(content);
  document.getElementById('dim-conflict').textContent = Math.round(tension.conflict * 100) + '%';
  document.getElementById('dim-suspense').textContent = Math.round(tension.suspense * 100) + '%';
  document.getElementById('dim-emotion').textContent = Math.round(tension.emotion * 100) + '%';
  document.getElementById('dim-rhythm').textContent = Math.round(tension.rhythm * 100) + '%';

  // 更新 DOME 时间线信息
  if (projectId) {
    try {
      const timeline = await api.getProjectTimeline(projectId, 10);
      const domeInfo = document.getElementById('batch-dome-info');
      if (domeInfo && timeline.events?.length > 0) {
        domeInfo.innerHTML = `已有${timeline.events.length}个事件`;
        domeInfo.style.color = '#4ade80';
      } else if (domeInfo) {
        domeInfo.innerHTML = '暂无事件记录';
        domeInfo.style.color = '#888';
      }

      // 更新 SCORE 角色状态
      const charStates = await api.getCharacterStates(projectId);
      const scoreInfo = document.getElementById('batch-score-info');
      if (scoreInfo && charStates.states?.length > 0) {
        scoreInfo.innerHTML = charStates.states.slice(0, 3).map(s =>
          `<div>${s.character_name}: ${s.emotion || '未知'}</div>`
        ).join('');
        scoreInfo.style.color = '#4ade80';
      } else if (scoreInfo) {
        scoreInfo.innerHTML = '暂无状态记录';
        scoreInfo.style.color = '#888';
      }

      // 更新 CFPG 伏笔信息
      const summary = await api.getProjectSummary(projectId);
      const foreshadowInfo = document.getElementById('batch-foreshadow-info');
      if (foreshadowInfo && summary.foreshadow) {
        const planted = summary.foreshadow.planted || 0;
        const triggered = summary.foreshadow.triggered || 0;
        foreshadowInfo.innerHTML = `埋设${planted}个, 触发${triggered}个`;
        foreshadowInfo.style.color = '#fbbf24';
      }

      // 更新 CoKe 套路信息
      const tropeWarning = await api.getTropeWarning(projectId, (session?.currentIndex || 0) + 1);
      const tropeInfo = document.getElementById('batch-trope-info');
      if (tropeInfo) {
        if (tropeWarning.has_warning) {
          tropeInfo.innerHTML = '⚠️ 有套路警告';
          tropeInfo.style.color = '#e94560';
        } else {
          tropeInfo.innerHTML = '✓ 暂无警告';
          tropeInfo.style.color = '#4ade80';
        }
      }

      // 更新 ConStory 一致性检查
      const consistency = await api.preWriteCheck(projectId);
      const consistencyInfo = document.getElementById('batch-consistency-info');
      if (consistencyInfo) {
        const highCount = consistency.warnings?.high?.length || 0;
        const mediumCount = consistency.warnings?.medium?.length || 0;
        if (highCount > 0) {
          consistencyInfo.innerHTML = `⚠️ ${highCount}个高危警告`;
          consistencyInfo.style.color = '#e94560';
        } else if (mediumCount > 0) {
          consistencyInfo.innerHTML = `⚡ ${mediumCount}个中危警告`;
          consistencyInfo.style.color = '#fbbf24';
        } else {
          consistencyInfo.innerHTML = '✓ 暂无警告';
          consistencyInfo.style.color = '#4ade80';
        }
      }
    } catch (e) {
      console.warn('[审核维度] 获取Continuity信息失败:', e);
    }
  }

  // 更新套路信息
  const tropeInfo = document.getElementById('batch-trope-info');
  if (tropeInfo) {
    const ck = ['怒', '吼', '骂', '吵', '争', '夺', '砸', '冷笑', '对峙'];
    const sk = ['突然', '忽然', '猛地', '难道', '究竟', '到底', '就在这时', '没想到', '然而'];
    const ek = ['愤怒', '悲伤', '恐惧', '惊讶', '心痛', '激动', '绝望', '爱', '恨'];
    const tropeCount = [...ck, ...sk, ...ek].filter(k => content.includes(k)).length;
    if (!tropeInfo.style.color || tropeInfo.style.color === 'rgb(136, 136, 136)') {
      tropeInfo.innerHTML = `检测到${tropeCount}个张力表达`;
    }
  }
}

document.addEventListener('DOMContentLoaded', init);
init();

/**
 * 写作模块 - 续写/润色/改写/概括
 */

// ============ 写作 ============
async function startWriting(instruction) {
  if (stateManager.state.isWriting) return;
  const content = document.getElementById('editor')?.value || '';
  stateManager.setIsWriting(true);
  stateManager.state.currentInstruction = instruction;

  const editor = document.getElementById('editor');
  updateWritingButtons();

  const statusEl = document.getElementById('writing-status');
  if (statusEl) {
    const labels = { '续写': '✍️ 正在续写...', '润色': '✍️ 正在润色...', '改写': '✍️ 正在改写...', '概括': '✍️ 正在概括...' };
    statusEl.textContent = labels[instruction] || '✍️ 正在生成...';
  }

  try {
    await api.writeStream(
      stateManager.state.currentChapter?.id || 'writing',
      instruction,
      content,
      {
        onChunk(content) {
          if (editor) {
            editor.value += content;
            updateWordCount();
          }
        },
        onDone() {
          const statusEl = document.getElementById('writing-status');
          if (statusEl) statusEl.textContent = '✅ 生成完成';
        },
        onError(msg) {
          console.error('写作错误:', msg);
          const statusEl = document.getElementById('writing-status');
          if (statusEl) statusEl.textContent = '❌ 错误: ' + msg;
        }
      }
    );
  } catch (e) {
    console.error('失败:', e);
    const statusEl = document.getElementById('writing-status');
    if (statusEl) statusEl.textContent = '❌ 请求失败: ' + e.message;
  } finally {
    stateManager.setIsWriting(false);
    updateWritingButtons();
    updateUI();
  }
}

function stopWriting() {
  stateManager.setIsWriting(false);
  updateWritingButtons();
  updateUI();
}

function updateWritingButtons() {
  const startPanel = document.getElementById('writing-start-panel');
  const iDiv = document.getElementById('writing-instructions');
  const cDiv = document.getElementById('writing-controls');
  const editor = document.getElementById('editor');
  const hasContent = editor && editor.value && editor.value.length > 0;

  if (stateManager.state.isWriting) {
    // 写作中：隐藏开始按钮和工具栏，显示停止控件
    if (startPanel) startPanel.style.display = 'none';
    if (iDiv) iDiv.style.display = 'none';
    if (cDiv) cDiv.style.display = 'flex';
  } else {
    // 非写作中：隐藏停止控件
    if (cDiv) cDiv.style.display = 'none';
    // 有内容时显示工具栏（续写/润色等），无内容时显示开始写作按钮
    if (hasContent) {
      if (startPanel) startPanel.style.display = 'none';
      if (iDiv) iDiv.style.display = 'flex';
    } else {
      if (startPanel) startPanel.style.display = 'block';
      if (iDiv) iDiv.style.display = 'none';
    }
  }
}

async function saveChapter() {
  if (!stateManager.state.currentChapter) return;
  const content = document.getElementById('editor')?.value || '';
  try {
    await api.saveChapterVersion(stateManager.state.currentChapter.id, content, '保存');
    await api.updateChapter(stateManager.state.currentChapter.id, {
      content,
      status: content.length > 100 ? 'writing' : 'draft'
    });
    await loadProjectData();
    alert('保存成功');
  } catch (e) { alert('保存失败: ' + e.message); }
}

// ============ 张力分析 ============
let tensionTimer = null;

function onEditorInput() {
  if (tensionTimer) clearTimeout(tensionTimer);
  tensionTimer = setTimeout(() => {
    analyzeRealtimeTension();
    updateWordCount();
    updateWritingButtons(); // 内容变化时更新按钮显示
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

// ============ 字数统计 ============
function updateWordCount() {
  const content = document.getElementById('editor')?.value || '';
  const count = content.replace(/\s/g, '').length;
  const wc = document.getElementById('word-count');
  if (wc) wc.textContent = count;
}

window.writingModule = {
  startWriting, stopWriting, updateWritingButtons, saveChapter,
  onEditorInput, analyzeRealtimeTension, localTensionAnalyze,
  updateRealtimeTensionDisplay, updateWordCount
};
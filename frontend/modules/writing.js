/**
 * 写作模块 - 续写/润色/改写/概括
 */

// ============ 写作 ============
async function startWriting(instruction) {
  if (stateManager.state.isWriting) return;
  const content = document.getElementById('editor')?.value || '';
  stateManager.setIsWriting(true);
  stateManager.state.currentInstruction = instruction;

  // ConStory一致性检查（仅续写且有项目时）
  if (instruction === '续写' && stateManager.state.currentProject?.id) {
    const checkResult = await runPreWriteCheck(stateManager.state.currentProject.id);
    if (checkResult && !showConStoryWarningDialog(checkResult)) {
      stateManager.setIsWriting(false);
      return; // 用户取消
    }
  }

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
        onDone(evt) {
          const statusEl = document.getElementById('writing-status');
          if (statusEl) statusEl.textContent = '✅ 生成完成';
          // 续写完成后自动分析（Continuity后处理）
          if (instruction === '续写' && stateManager.state.currentChapter?.id) {
            const content = editor?.value || '';
            schedulePostWriteAnalysis(stateManager.state.currentChapter.id, content);
          }
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

// ============ 续写后自动分析 ============
let analyzeTimer = null;

async function runPreWriteCheck(projectId) {
  try {
    const result = await api.preWriteCheck(projectId);
    return result;
  } catch (e) {
    console.error('[ConStory] 检查失败:', e);
    return null;
  }
}

function showConStoryWarningDialog(checkResult) {
  const warnings = checkResult?.warnings || {};
  const high = warnings.high || [];
  const medium = warnings.medium || [];

  if (high.length === 0 && medium.length === 0) {
    return true; // 无严重警告，直接继续
  }

  const messages = [];
  high.forEach(w => messages.push(`⚠️ 高危: ${w.message}`));
  medium.forEach(w => messages.push(`⚡ 中危: ${w.message}`));

  return confirm(`[ConStory 一致性警告]\n\n${messages.join('\n')}\n\n是否继续写作？（取消后可调整角色状态）`);
}

function schedulePostWriteAnalysis(chapterId, content) {
  // 写作完成后延迟2秒，确保章节已保存
  if (analyzeTimer) clearTimeout(analyzeTimer);
  analyzeTimer = setTimeout(async () => {
    try {
      console.log('[Continuity] 开始分析章节:', chapterId);
      const result = await api.analyzeChapter(chapterId, content);
      console.log('[Continuity] 分析完成:', result);
      // 可以在这里触发UI更新，比如显示连贯性摘要
      if (window.app && window.app.refreshContinuity) {
        window.app.refreshContinuity();
      }
    } catch (e) {
      console.error('[Continuity] 分析失败:', e);
    }
  }, 2000);
}

// ============ BVSR/SWAG 必须事件 ============
const swagAnchors = [];

function addSwagAnchor(eventText) {
  if (eventText && !swagAnchors.includes(eventText)) {
    swagAnchors.push(eventText);
    updateSwagAnchorsDisplay();
  }
}

function removeSwagAnchor(eventText) {
  const idx = swagAnchors.indexOf(eventText);
  if (idx > -1) {
    swagAnchors.splice(idx, 1);
    updateSwagAnchorsDisplay();
  }
}

function updateSwagAnchorsDisplay() {
  const container = document.getElementById('swag-anchors-list');
  if (!container) return;
  if (swagAnchors.length === 0) {
    container.innerHTML = '<span style="color:#888;font-size:12px">暂无必须事件</span>';
  } else {
    container.innerHTML = swagAnchors.map((e, i) =>
      `<span class="swag-anchor-item" title="点击移除">${escapeHtml(e)} <button onclick="writingModule.removeSwagAnchor('${escapeHtml(e).replace(/'/g, "\\'")}')" style="background:none;border:none;color:#f44;cursor:pointer;padding:0 2px">×</button></span>`
    ).join('');
  }
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

window.writingModule = {
  startWriting, stopWriting, updateWritingButtons, saveChapter,
  onEditorInput, analyzeRealtimeTension, localTensionAnalyze,
  updateRealtimeTensionDisplay, updateWordCount,
  // Continuity
  schedulePostWriteAnalysis,
  // BVSR/SWAG
  addSwagAnchor, removeSwagAnchor, getSwagAnchors: () => [...swagAnchors]
};
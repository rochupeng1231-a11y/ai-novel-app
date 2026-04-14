/**
 * API 客户端 - 所有后端请求
 */
const API_BASE = 'http://localhost:8000/api';

// ============ 项目 ============
async function apiCreateProject(name, targetWordCount = 300000) {
  const res = await fetch(`${API_BASE}/db/projects`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, description: '', target_word_count: targetWordCount})
  });
  return res.json();
}

async function apiGetProjects() {
  const res = await fetch(`${API_BASE}/db/projects`);
  return res.json();
}

async function apiDeleteProject(projectId) {
  await fetch(`${API_BASE}/db/projects/${projectId}`, { method: 'DELETE' });
}

async function apiUpdateProject(projectId, data) {
  const res = await fetch(`${API_BASE}/db/projects/${projectId}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  return res.json();
}

// ============ 章节 ============
async function apiCreateChapter(projectId, number, title) {
  const res = await fetch(`${API_BASE}/db/chapters`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({project_id: projectId, number, title})
  });
  return res.json();
}

async function apiUpdateChapter(chapterId, data) {
  const res = await fetch(`${API_BASE}/db/chapters/${chapterId}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  return res.json();
}

async function apiSaveChapterVersion(chapterId, content, changeSummary = '') {
  await fetch(`${API_BASE}/db/chapters/${chapterId}/versions`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chapter_id: chapterId, content, change_summary: changeSummary})
  });
}

// ============ 角色 ============
async function apiCreateCharacter(projectId, data) {
  const res = await fetch(`${API_BASE}/db/characters`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({project_id: projectId, ...data})
  });
  return res.json();
}

// ============ 伏笔 ============
async function apiCreateForeshadow(projectId, keyword, description, status = 'planted') {
  const body = {project_id: projectId, keyword, description, status};
  const res = await fetch(`${API_BASE}/db/foreshadows`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`创建伏笔失败(${res.status}): ${err}`);
  }
  return res.json();
}

// ============ 写作（SSE流式） ============
/**
 * 流式写作请求
 * @param {string} chapterId - 章节ID或'outline'
 * @param {string} instruction - 续写/润色/改写/概括/大纲
 * @param {string} context - 上下文内容
 * @param {object} callbacks - {onChunk, onDone, onError}
 */
async function apiWriteStream(chapterId, instruction, context, callbacks) {
  const response = await fetch(`${API_BASE}/writing/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chapter_id: chapterId, instruction, context: context || ''})
  });

  if (!response.ok) {
    throw new Error(`请求失败: HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let totalChunks = 0;
  let totalBytes = 0;

  let doneCalled = false;

  // 处理一行 SSE 数据
  function processLine(line) {
    const trimmed = line.trim();
    if (!trimmed || trimmed === '[DONE]') return;

    if (trimmed.startsWith('data: ')) {
      const dataStr = trimmed.slice(6).trim();
      if (dataStr === '[DONE]') {
        doneCalled = true;
        callbacks.onDone && callbacks.onDone();
        return;
      }
      try {
        const evt = JSON.parse(dataStr);
        if (evt.type === 'chunk' && evt.content) {
          callbacks.onChunk && callbacks.onChunk(evt.content);
        } else if (evt.type === 'done') {
          doneCalled = true;
          callbacks.onDone && callbacks.onDone(evt);
        } else if (evt.type === 'error') {
          const msg = evt.message || evt.error?.message || '';
          if (msg.includes('529') || msg.includes('overloaded') || msg.includes('服务集群负载较高')) {
            callbacks.onError && callbacks.onError('⚠️ MiniMax服务繁忙（负载过高），请1-2分钟后重试。');
          } else {
            callbacks.onError && callbacks.onError(msg);
          }
        }
      } catch (e) {
        console.warn('[SSE] 解析失败:', dataStr.substring(0, 100));
      }
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    totalChunks++;
    totalBytes += value.byteLength;
    buffer += decoder.decode(value, { stream: true });

    // 处理所有完整的行
    while (buffer.includes('\n')) {
      const newlineIndex = buffer.indexOf('\n');
      const line = buffer.substring(0, newlineIndex);
      buffer = buffer.substring(newlineIndex + 1);
      processLine(line);
    }
  }

  // 处理缓冲区中剩余的数据（最后一行可能没有换行符）
  if (buffer.trim()) {
    processLine(buffer);
  }

  console.log(`[SSE] 完成: ${totalChunks} 个 chunk, 共 ${totalBytes} bytes`);

  // 流结束后确保 onDone 被调用
  if (!doneCalled) {
    callbacks.onDone && callbacks.onDone();
  }
}

// ============ 连贯性（Continuity） ============
async function apiAnalyzeChapter(chapterId, chapterContent = null) {
  const body = {chapter_id: chapterId};
  if (chapterContent !== null) body.chapter_content = chapterContent;
  const res = await fetch(`${API_BASE}/continuity/analyze`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`分析失败: ${res.status}`);
  return res.json();
}

async function apiPreWriteCheck(projectId) {
  const res = await fetch(`${API_BASE}/continuity/check/${projectId}`);
  if (!res.ok) throw new Error(`一致性检查失败: ${res.status}`);
  return res.json();
}

async function apiUpdateCharacterState(chapterId, characterId, updateData) {
  const res = await fetch(`${API_BASE}/continuity/state/update?chapter_id=${chapterId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({character_id: characterId, ...updateData})
  });
  if (!res.ok) throw new Error(`更新状态失败: ${res.status}`);
  return res.json();
}

async function apiGetProjectSummary(projectId) {
  const res = await fetch(`${API_BASE}/continuity/summary/${projectId}`);
  if (!res.ok) throw new Error(`获取摘要失败: ${res.status}`);
  return res.json();
}

async function apiGetProjectTimeline(projectId, limit = 50) {
  const res = await fetch(`${API_BASE}/continuity/timeline/${projectId}?limit=${limit}`);
  if (!res.ok) throw new Error(`获取时间线失败: ${res.status}`);
  return res.json();
}

async function apiGetCharacterStates(projectId) {
  const res = await fetch(`${API_BASE}/continuity/character_states/${projectId}`);
  if (!res.ok) throw new Error(`获取角色状态失败: ${res.status}`);
  return res.json();
}

async function apiGetTropeWarning(projectId, chapterNumber = 1) {
  const res = await fetch(`${API_BASE}/continuity/trope/warning/${projectId}?chapter_number=${chapterNumber}`);
  if (!res.ok) throw new Error(`获取套路警告失败: ${res.status}`);
  return res.json();
}

async function apiPlantForeshadowFromOutline(projectId, outline, firstChapterId = null) {
  const body = {project_id: projectId, outline};
  if (firstChapterId) body.first_chapter_id = firstChapterId;
  const res = await fetch(`${API_BASE}/continuity/foreshadow/from_outline`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`埋设伏笔失败: ${res.status}`);
  return res.json();
}

// ============ 批量写作 API ============
async function apiBatchWriteStart(projectId, chapterIds, instruction = '续写') {
  const res = await fetch(`${API_BASE}/writing/batch/start`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({project_id: projectId, chapter_ids: chapterIds, instruction})
  });
  if (!res.ok) throw new Error(`批量写作启动失败: ${res.status}`);
  return res.json();
}

async function apiBatchWriteGetNextChapter(batchId) {
  // 获取下一章节信息
  const res = await fetch(`${API_BASE}/writing/batch/${batchId}/next-chapter`);
  if (!res.ok) throw new Error(`获取下一章失败: ${res.status}`);
  return res.json();
}

async function apiBatchWriteCompleteChapter(batchId, chapterId, content, tensionScore) {
  // 标记章节写作完成
  const res = await fetch(`${API_BASE}/writing/batch/${batchId}/complete-chapter`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chapter_id: chapterId, content, tension_score: tensionScore})
  });
  if (!res.ok) throw new Error(`完成章节失败: ${res.status}`);
  return res.json();
}

async function apiBatchWriteReview(batchId, action, content = null) {
  const body = {action};
  if (content) body.content = content;
  const res = await fetch(`${API_BASE}/writing/batch/${batchId}/review`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`审核操作失败: ${res.status}`);
  return res.json();
}

async function apiBatchWriteStatus(batchId) {
  const res = await fetch(`${API_BASE}/writing/batch/${batchId}/status`);
  if (!res.ok) throw new Error(`获取批量写作状态失败: ${res.status}`);
  return res.json();
}

window.api = {
  createProject: apiCreateProject,
  getProjects: apiGetProjects,
  deleteProject: apiDeleteProject,
  updateProject: apiUpdateProject,
  createChapter: apiCreateChapter,
  updateChapter: apiUpdateChapter,
  saveChapterVersion: apiSaveChapterVersion,
  createCharacter: apiCreateCharacter,
  createForeshadow: apiCreateForeshadow,
  writeStream: apiWriteStream,
  // Continuity
  analyzeChapter: apiAnalyzeChapter,
  preWriteCheck: apiPreWriteCheck,
  updateCharacterState: apiUpdateCharacterState,
  getProjectSummary: apiGetProjectSummary,
  getProjectTimeline: apiGetProjectTimeline,
  getCharacterStates: apiGetCharacterStates,
  getTropeWarning: apiGetTropeWarning,
  plantForeshadowFromOutline: apiPlantForeshadowFromOutline,
  // 批量写作
  batchWriteStart: apiBatchWriteStart,
  batchWriteGetNextChapter: apiBatchWriteGetNextChapter,
  batchWriteCompleteChapter: apiBatchWriteCompleteChapter,
  batchWriteReview: apiBatchWriteReview,
  batchWriteStatus: apiBatchWriteStatus
};
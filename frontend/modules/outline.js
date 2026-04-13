/**
 * 大纲生成模块
 */
let selectedType = null;
let selectedElements = [];

// ============ 类型/元素选择 ============
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

function backToProject() {
  selectedType = null;
  selectedElements = [];
  stateManager.setStep('project');
  stateManager.setCurrentProject(null);
  updateUI();
}

// ============ 渲染选择界面 ============
function renderOutlineSelect() {
  const typeGrid = document.getElementById('type-grid');
  const elementGrid = document.getElementById('element-grid');
  if (!typeGrid || !elementGrid) return;

  typeGrid.innerHTML = NOVEL_TYPES.map(t => `
    <div class="type-card" onclick="app.selectNovelType('${t.id}')">
      <div style="font-size:24px;margin-bottom:8px">${t.icon}</div>
      <div style="font-weight:600;font-size:14px">${t.name}</div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">${t.desc}</div>
    </div>
  `).join('');

  elementGrid.innerHTML = CORE_ELEMENTS.map(el => `
    <div class="element-tag" onclick="app.toggleElement('${el}')">${el}</div>
  `).join('');
}

// ============ 生成大纲 ============
// 分两步：1.先生成基本大纲 2.逐章生成简介
async function generateOutline() {
  if (!selectedType) { alert('请选类型'); return; }
  showOutlineLoading();

  const elements = selectedElements.length > 0 ? selectedElements.join('、') : '热血激情';
  const outlineChunks = [];

  // 第一步：生成基本大纲（故事主线 + 人物 + 章节标题 + 关系 + 伏笔）
  const basicPrompt = `小说类型：【${selectedType.name}】，核心元素：${elements}。

请生成完整大纲，必须包含以下5个部分：
1. 故事主线（1-2段）
2. 主要人物（3-5个）
3. 章节结构（8-12章）
4. 角色关系
5. 重要伏笔（3-5个）

格式简洁即可，未完成全部5个部分之前不要停止生成！`;

  let hasError = false;
  try {
    await api.writeStream('outline', '大纲', basicPrompt, {
      onChunk(content) {
        outlineChunks.push(content);
        const previewArea = document.getElementById('outline-preview-area');
        if (previewArea) {
          previewArea.style.display = 'block';
          previewArea.textContent = outlineChunks.join('');
          previewArea.scrollTop = previewArea.scrollHeight;
        }
        setProgressInline(40, 'AI 正在生成基本大纲...');
      },
      onDone(evt) {
        if (evt && evt.tension_score !== undefined) {
          console.log('[大纲] 基本大纲完成，张力:', evt.tension_score);
        }
      },
      onError(msg) {
        console.error('[大纲] SSE错误:', msg);
        hasError = true;
        alert('生成失败：' + msg);
        showOutlineSelect();
      }
    });
  } catch (e) {
    console.error('[大纲] 请求失败:', e);
    hasError = true;
    alert('生成失败：' + e.message);
    showOutlineSelect();
    return;
  }

  if (hasError) return;

  const outlineContent = outlineChunks.join('');
  console.log('[大纲] 完成，基本大纲长度:', outlineContent.length);

  if (!outlineContent || outlineContent.length < 50) {
    alert('生成失败：AI返回内容为空，请检查网络或API配置');
    showOutlineSelect();
    return;
  }

  // 先创建章节
  setProgressInline(60, '正在创建章节...');
  const chapters = parseChaptersFromOutline(outlineContent);
  for (const ch of chapters) {
    try {
      await api.createChapter(stateManager.state.currentProject.id, ch.num, ch.title);
    } catch (e) { console.error('创建章节失败', e); }
  }

  // 解析角色
  const characters = parseCharactersFromOutline(outlineContent);
  const createdCharacters = [];
  for (const c of characters) {
    try {
      const char = await api.createCharacter(stateManager.state.currentProject.id, {
        name: c.name,
        personality: c.personality || '',
        alias: '',
        speech_style: '',
        forbidden_topics: []
      });
      createdCharacters.push(char);
    } catch (e) { console.error('创建角色失败', e); }
  }

  // 构建角色名到ID的映射
  const characterMap = {};
  createdCharacters.forEach(c => { characterMap[c.name] = c.id; });
  console.log('[角色] 映射表:', characterMap);

  // 重新加载数据
  await projectModule.loadProjectData();

  // 解析并创建角色关系
  const relations = parseRelationsFromOutline(outlineContent, characterMap);
  for (const r of relations) {
    try {
      await fetch(`${API_BASE}/relations`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          project_id: stateManager.state.currentProject.id,
          character_a_id: r.character_a_id,
          character_b_id: r.character_b_id,
          relation_type: r.relation_type,
          description: ''
        })
      });
    } catch (e) { console.error('创建关系失败', e); }
  }

  // 解析并创建伏笔
  const foreshadows = parseForeshadowsFromOutline(outlineContent);
  for (const f of foreshadows) {
    try {
      await api.createForeshadow(stateManager.state.currentProject.id, f.keyword, f.description, f.status);
    } catch (e) { console.error('创建伏笔失败', e); }
  }

  // 保存项目信息（类型、元素、大纲）到数据库
  try {
    await api.updateProject(stateManager.state.currentProject.id, {
      novel_type: selectedType.name,
      core_elements: JSON.stringify(selectedElements),
      outline: outlineContent
    });
    console.log('[大纲] 项目信息已保存');
  } catch (e) {
    console.error('[大纲] 保存项目信息失败', e);
  }

  // 第二步：逐章生成简介（分批，每批3章）
  setProgressInline(70, '正在生成章节简介（分批）...');
  const chapterList = stateManager.state.chapters;

  for (let i = 0; i < chapterList.length; i += 3) {
    const batch = chapterList.slice(i, i + 3);
    const batchNum = Math.floor(i / 3) + 1;
    setProgressInline(70 + Math.floor((i / chapterList.length) * 25), `生成章节简介（第${batchNum}批/${Math.ceil(chapterList.length/3)}批）...`);

    const batchContext = batch.map(ch => `第${ch.number}章 ${ch.title}`).join('、');

    // 向后端请求章节简介（这里用同一个writeStream，但发送章节ID列表让后端处理）
    // 由于后端不支持按章节ID列表生成，我们暂时跳过这步，用户可以在写作界面自行查看章节标题
    console.log('[章节简介] 批次', batchNum, ':', batchContext);
  }

  stateManager.setOutline({type: selectedType.name, content: outlineContent, created_at: new Date().toISOString()});
  setProgressInline(100, '完成！');
  stateManager.setStep('chapters');
  updateUI();
}

// 从大纲文本解析章节列表
function parseChaptersFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const lines = clean.split('\n');
  const chapters = [];
  let currentChapterNum = null;
  let currentChapterTitle = null;

  for (const line of lines) {
    const trimmed = line.trim();
    const chMatch = /^第[一二三四五六七八九十百零\d]+章[：:](.*)$/.exec(trimmed);
    if (chMatch) {
      if (currentChapterNum !== null && currentChapterTitle !== null) {
        chapters.push({num: currentChapterNum, title: currentChapterTitle});
      }
      currentChapterNum = chapters.length + 1;
      currentChapterTitle = chMatch[1].trim() || `第${currentChapterNum}章`;
    }
  }
  if (currentChapterNum !== null && currentChapterTitle !== null) {
    chapters.push({num: currentChapterNum, title: currentChapterTitle});
  }
  console.log('[解析] 章节数量:', chapters.length);
  return chapters;
}

// 从大纲文本解析角色列表
function parseCharactersFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const characters = [];

  // 尝试多种格式
  const patterns = [
    /(?:主要人物|人物|角色)[：:]*\n?([\s\S]*?)(?:章节结构|$)/i,
    /(?:\d+[.、]\s*)(.{2,8}?)(?:，|,|\s*[-—–])\s*([^。\n]{2,50}?)(?=[。\n]|$)/gm,
  ];

  for (const pattern of patterns) {
    const match = pattern.exec(clean);
    if (match) {
      const charText = match[1] || match[0];
      const charLines = charText.split('\n');
      for (const cl of charLines) {
        const ctrim = cl.trim();
        if (!ctrim || ctrim.length < 4) continue;
        const nameMatch = /^(.{2,8})[-—–:,，、.\s](.{3,50})/.exec(ctrim);
        if (nameMatch) {
          const name = nameMatch[1].replace(/[^A-Za-z\u4e00-\u9fa5]/g, '');
          const personality = nameMatch[2].replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '').trim();
          if (name.length >= 2 && personality.length >= 2) {
            characters.push({name, personality});
          }
        }
      }
      if (characters.length > 0) break;
    }
  }
  console.log('[解析] 角色数量:', characters.length);
  return characters;
}

// 从大纲文本解析角色关系
function parseRelationsFromOutline(outline, characterMap) {
  // characterMap: { name: id } 从角色名到ID的映射
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const relations = [];

  // 匹配 "角色A —关系— 角色B" 或 "角色A - 关系 - 角色B" 等格式
  const relPattern = /([^\s—–-]{2,8})\s*[—–-]{1,3}\s*([^\s—–-]{2,8})\s*[—–-]{1,3}\s*([^\s—–-]{2,8})/g;
  let match;
  while ((match = relPattern.exec(clean)) !== null) {
    const charA = match[1].trim();
    const relType = match[2].trim();
    const charB = match[3].trim();

    if (characterMap[charA] && characterMap[charB]) {
      relations.push({
        character_a_id: characterMap[charA],
        character_b_id: characterMap[charB],
        relation_type: relType
      });
    }
  }

  console.log('[解析] 关系数量:', relations.length);
  return relations;
}

// 从大纲文本解析伏笔
function parseForeshadowsFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const foreshadows = [];

  // 匹配 "关键词|描述|状态" 格式
  const fsPattern = /([^\s|]{2,10})\s*\|\s*([^|]{5,50})\s*\|\s*(\([^)]+\))/g;
  let match;
  while ((match = fsPattern.exec(clean)) !== null) {
    const keyword = match[1].trim();
    const description = match[2].trim();
    let status = match[3].trim();

    // 解析状态
    if (status.includes('已埋') || status.includes('pending')) {
      status = 'planted';
    } else if (status.includes('已触发') || status.includes('triggered')) {
      status = 'triggered';
    } else if (status.includes('已回收') || status.includes('resolved')) {
      status = 'resolved';
    } else {
      status = 'planted';
    }

    foreshadows.push({ keyword, description, status });
  }

  console.log('[解析] 伏笔数量:', foreshadows.length);
  return foreshadows;
}

function showOutlineSelect() {
  document.getElementById('outline-select-panel').style.display = 'block';
  document.getElementById('outline-loading-panel').style.display = 'none';
}

function showOutlineLoading() {
  document.getElementById('outline-select-panel').style.display = 'none';
  document.getElementById('outline-loading-panel').style.display = 'flex';
  setProgressInline(5, '正在请求 AI 生成大纲...');
}

function regenerateOutline() {
  selectedType = null;
  selectedElements = [];
  stateManager.setStep('outline');
  updateUI();
}

window.outlineModule = {
  selectNovelType, toggleElement, backToProject,
  renderOutlineSelect, generateOutline, regenerateOutline,
  showOutlineSelect, showOutlineLoading
};
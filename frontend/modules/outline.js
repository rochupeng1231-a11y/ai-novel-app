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

// ============ 生成大纲（增量模式） ============
// 分阶段生成，每阶段独立，失败只需重试该阶段
async function generateOutline() {
  if (!selectedType) { alert('请选类型'); return; }
  showOutlineLoading();

  const elements = selectedElements.length > 0 ? selectedElements.join('、') : '热血激情';
  const projectId = stateManager.state.currentProject.id;

  try {
    // ========== 阶段 1: 生成故事主线 ==========
    setProgressInline(5, '生成故事主线...');
    const mainPlotPrompt = `小说类型：【${selectedType.name}】，核心元素：${elements}。

请生成故事主线（1-2段），描述：
- 故事的核心冲突是什么
- 主线情节走向
- 最终目标或结局方向

请直接输出故事主线，不要其他格式。`;

    let mainPlot = '';
    let stage1Error = false;
    await api.writeStream('outline', '大纲', mainPlotPrompt, {
      onChunk(content) { mainPlot += content; },
      onDone() { console.log('[阶段1] 故事主线完成，长度:', mainPlot.length); },
      onError(msg) {
        console.error('[阶段1] 失败:', msg);
        alert('生成故事主线失败：' + msg);
        stage1Error = true;
        showOutlineSelect();
      }
    });
    if (stage1Error) return;
    if (!mainPlot || mainPlot.length < 20) {
      alert('生成失败：故事主线太短，请重试');
      showOutlineSelect();
      return;
    }

    // ========== 阶段 2: 生成章节标题 ==========
    setProgressInline(20, '生成章节标题...');
    const chaptersPrompt = `基于以下故事主线，生成8-12章的章节标题：

${mainPlot}

【输出格式】（必须严格按此格式）
每行一章：第1章 标题
第2章 标题
...

不要加任何其他内容。`;

    let chaptersText = '';
    let stage2Error = false;
    await api.writeStream('outline', '章节', chaptersPrompt, {
      onChunk(content) { chaptersText += content; },
      onDone() { console.log('[阶段2] 章节标题完成，长度:', chaptersText.length); },
      onError(msg) {
        console.error('[阶段2] 失败:', msg);
        alert('生成章节标题失败：' + msg);
        stage2Error = true;
        showOutlineSelect();
      }
    });
    if (stage2Error) return;

    // 解析并创建章节
    setProgressInline(30, '创建章节...');
    const chapters = parseChaptersFromOutline(chaptersText);
    if (chapters.length < 3) {
      alert('生成失败：章节数量太少（' + chapters.length + '），请重试');
      showOutlineSelect();
      return;
    }
    for (const ch of chapters) {
      try {
        await api.createChapter(projectId, ch.num, ch.title);
      } catch (e) { console.error('[创建章节]', ch.num, ch.title, '失败:', e); }
    }
    console.log('[阶段2] 已创建', chapters.length, '个章节');

    // ========== 阶段 3: 生成角色列表 ==========
    setProgressInline(40, '生成角色列表...');
    const charactersPrompt = `基于以下故事主线，生成3-5个主要角色：

${mainPlot}

【输出格式】（必须严格按此格式，JSON数组）
[
  {"name": "角色名1", "personality": "性格描述"},
  {"name": "角色名2", "personality": "性格描述"}
]

只输出JSON数组，不要其他内容。`;

    let charactersText = '';
    let stage3Error = false;
    await api.writeStream('outline', '大纲', charactersPrompt, {
      onChunk(content) { charactersText += content; },
      onDone() { console.log('[阶段3] 角色列表完成，长度:', charactersText.length); },
      onError(msg) {
        console.error('[阶段3] 失败:', msg);
        alert('生成角色列表失败：' + msg);
        stage3Error = true;
        showOutlineSelect();
      }
    });
    if (stage3Error) return;

    // 解析并创建角色
    const characters = parseCharactersFromOutline(charactersText);
    const createdCharacters = [];
    for (const c of characters) {
      if (!c.name) continue;
      try {
        const char = await api.createCharacter(projectId, {
          name: c.name,
          personality: c.personality || '',
          alias: '',
          speech_style: '',
          forbidden_topics: []
        });
        createdCharacters.push(char);
      } catch (e) { console.error('[创建角色]', c.name, '失败:', e); }
    }
    console.log('[阶段3] 已创建', createdCharacters.length, '个角色');

    // 构建角色名到ID的映射
    const characterMap = {};
    createdCharacters.forEach(c => { characterMap[c.name] = c.id; });

    // ========== 阶段 4: 生成角色关系 ==========
    setProgressInline(60, '生成角色关系...');
    const relationsPrompt = `基于以下故事主线和角色列表，分析角色之间的关系：

故事主线：
${mainPlot}

角色：
${createdCharacters.map(c => `- ${c.name}（${c.personality || '未知'}）`).join('\n')}

【输出格式】（必须严格按此格式，JSON数组）
[
  {"charA": "角色A", "charB": "角色B", "relation": "关系类型"},
  {"charA": "角色B", "charB": "角色C", "relation": "关系类型"}
]

关系类型包括：朋友、敌人、爱人、师徒、家人、竞争对手等。
只输出JSON数组，不要其他内容。`;

    let relationsText = '';
    let stage4Error = false;
    await api.writeStream('outline', '大纲', relationsPrompt, {
      onChunk(content) { relationsText += content; },
      onDone() { console.log('[阶段4] 角色关系完成，长度:', relationsText.length); },
      onError(msg) {
        console.error('[阶段4] 失败:', msg);
        // 关系生成失败不影响主流程，继续执行
        console.log('[阶段4] 继续执行，不阻塞流程');
      }
    });

    // 解析并创建角色关系
    if (relationsText) {
      const relations = parseRelationsFromOutline(relationsText, characterMap);
      for (const r of relations) {
        if (!r.character_a_id || !r.character_b_id) continue;
        try {
          await fetch(`${API_BASE}/db/relations`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              project_id: projectId,
              character_a_id: r.character_a_id,
              character_b_id: r.character_b_id,
              relation_type: r.relation_type,
              description: ''
            })
          });
        } catch (e) { console.error('[创建关系]', r, '失败:', e); }
      }
      console.log('[阶段4] 已创建关系', relations.length, '条');
    }

    // ========== 阶段 5: 生成伏笔 ==========
    setProgressInline(75, '生成伏笔...');
    const foreshadowsPrompt = `基于以下故事主线，设计3-5个重要伏笔：

${mainPlot}

【输出格式】（必须严格按此格式，JSON数组）
[
  {"keyword": "伏笔关键词", "description": "伏笔描述", "status": "planted"},
  {"keyword": "伏笔关键词2", "description": "伏笔描述2", "status": "planted"}
]

状态说明：planted=已埋下，triggered=已触发，resolved=已回收。
只输出JSON数组，不要其他内容。`;

    let foreshadowsText = '';
    let stage5Error = false;
    await api.writeStream('outline', '大纲', foreshadowsPrompt, {
      onChunk(content) { foreshadowsText += content; },
      onDone() { console.log('[阶段5] 伏笔完成，长度:', foreshadowsText.length); },
      onError(msg) {
        console.error('[阶段5] 失败:', msg);
        console.log('[阶段5] 继续执行，不阻塞流程');
      }
    });

    // 解析并创建伏笔
    if (foreshadowsText) {
      const foreshadows = parseForeshadowsFromOutline(foreshadowsText);
      for (const f of foreshadows) {
        if (!f.keyword) continue;
        try {
          await api.createForeshadow(projectId, f.keyword, f.description || '', f.status || 'planted');
        } catch (e) { console.error('[创建伏笔]', f, '失败:', e); }
      }
      console.log('[阶段5] 已创建伏笔', foreshadows.length, '个');
    }

    // ========== 保存项目信息 ==========
    setProgressInline(90, '保存项目信息...');
    const fullOutline = `【故事主线】\n${mainPlot}\n\n【章节结构】\n${chaptersText}`;
    try {
      await api.updateProject(projectId, {
        novel_type: selectedType.name,
        core_elements: JSON.stringify(selectedElements),
        outline: fullOutline
      });
      console.log('[保存] 项目信息已保存');
    } catch (e) {
      console.error('[保存] 项目信息保存失败:', e);
    }

    // 重新加载数据
    await projectModule.loadProjectData();

    stateManager.setOutline({
      type: selectedType.name,
      content: fullOutline,
      mainPlot: mainPlot,
      created_at: new Date().toISOString()
    });

    setProgressInline(100, '完成！');
    stateManager.setStep('chapters');
    updateUI();

  } catch (e) {
    console.error('[大纲] 生成过程异常:', e);
    alert('生成失败：' + e.message);
    showOutlineSelect();
  }
}

// 从大纲文本解析章节列表
function parseChaptersFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const lines = clean.split('\n');
  const chapters = [];
  let currentChapterNum = null;
  let currentChapterTitle = null;

  // 支持多种格式：第X章、第X章：标题、Ch.X、# 第X章 等
  const patterns = [
    /^第[一二三四五六七八九十百零\d]+章[：:]?\s*(.+)$/,
    /^Ch?\.?\s*(\d+)[：:\s](.+)$/i,
    /^#+\s*第?[一二三四五六七八九十百零\d]+章[：:]?\s*(.+)$/,
    /^[第]?\s*(\d+)\s*[章节章][：:\s](.+)$/,
  ];

  for (const line of lines) {
    const trimmed = line.trim();
    for (const pattern of patterns) {
      const match = pattern.exec(trimmed);
      if (match) {
        if (currentChapterNum !== null && currentChapterTitle !== null) {
          chapters.push({num: currentChapterNum, title: currentChapterTitle});
        }
        currentChapterNum = chapters.length + 1;
        // match[1] 可能是章节号或标题，取决于正则
        if (match.length === 3) {
          currentChapterTitle = (match[1].trim() || `第${currentChapterNum}章`);
        } else {
          currentChapterTitle = match[1].trim() || `第${currentChapterNum}章`;
        }
        break;
      }
    }
  }
  if (currentChapterNum !== null && currentChapterTitle !== null) {
    chapters.push({num: currentChapterNum, title: currentChapterTitle});
  }
  console.log('[解析] 章节数量:', chapters.length);
  return chapters;
}

// 从大纲文本解析角色列表（支持 JSON 和正则两种格式）
function parseCharactersFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const characters = [];

  // 方法1：尝试 JSON 解析
  try {
    const jsonMatch = clean.match(/\[[\s\S]*?\]/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (Array.isArray(parsed) && parsed.length > 0) {
        for (const item of parsed) {
          if (item.Name || item.name) {
            characters.push({
              name: (item.Name || item.name).replace(/[^A-Za-z\u4e00-\u9fa5]/g, ''),
              personality: (item.Personality || item.personality || '').replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, '')
            });
          }
        }
        if (characters.length > 0) {
          console.log('[解析] 角色(JSON):', characters.length);
          return characters;
        }
      }
    }
  } catch (e) {
    console.log('[解析] JSON解析失败，使用正则回退');
  }

  // 方法2：正则解析（多种格式）
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
  console.log('[解析] 角色(正则):', characters.length);
  return characters;
}

// 从大纲文本解析角色关系（支持 JSON 和正则两种格式）
function parseRelationsFromOutline(outline, characterMap) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const relations = [];

  // 方法1：尝试 JSON 解析
  try {
    const jsonMatch = clean.match(/\[[\s\S]*?\]/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (Array.isArray(parsed) && parsed.length > 0) {
        for (const item of parsed) {
          const charAName = item.charA || item.Name || item.name || '';
          const charBName = item.charB || item.Name2 || item.name2 || '';
          const relType = item.relation || item.Relation || '';

          if (characterMap[charAName] && characterMap[charBName]) {
            relations.push({
              character_a_id: characterMap[charAName],
              character_b_id: characterMap[charBName],
              relation_type: relType
            });
          }
        }
        if (relations.length > 0) {
          console.log('[解析] 关系(JSON):', relations.length);
          return relations;
        }
      }
    }
  } catch (e) {
    console.log('[解析] 关系JSON解析失败，使用正则回退');
  }

  // 方法2：正则解析
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

  console.log('[解析] 关系(正则):', relations.length);
  return relations;
}

// 从大纲文本解析伏笔（支持 JSON 和正则两种格式）
function parseForeshadowsFromOutline(outline) {
  const clean = outline.replace(/<[^>]+>/g, '').replace(/\*\*/g, '');
  const foreshadows = [];

  // 方法1：尝试 JSON 解析
  try {
    const jsonMatch = clean.match(/\[[\s\S]*?\]/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (Array.isArray(parsed) && parsed.length > 0) {
        for (const item of parsed) {
          const keyword = item.keyword || item.Keyword || item.name || '';
          const description = item.description || item.Description || '';
          let status = (item.status || item.Status || 'planted').toLowerCase();

          if (status.includes('trigger') || status.includes('触发')) {
            status = 'triggered';
          } else if (status.includes('resolve') || status.includes('回收')) {
            status = 'resolved';
          } else {
            status = 'planted';
          }

          if (keyword) {
            foreshadows.push({ keyword, description, status });
          }
        }
        if (foreshadows.length > 0) {
          console.log('[解析] 伏笔(JSON):', foreshadows.length);
          return foreshadows;
        }
      }
    }
  } catch (e) {
    console.log('[解析] 伏笔JSON解析失败，使用正则回退');
  }

  // 方法2：正则解析
  const fsPattern = /([^\s|]{2,10})\s*\|\s*([^|]{5,50})\s*\|\s*(\([^)]+\))/g;
  let match;
  while ((match = fsPattern.exec(clean)) !== null) {
    const keyword = match[1].trim();
    const description = match[2].trim();
    let status = match[3].trim();

    if (status.includes('已埋') || status.includes('pending') || status.includes('plant')) {
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

  console.log('[解析] 伏笔(正则):', foreshadows.length);
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
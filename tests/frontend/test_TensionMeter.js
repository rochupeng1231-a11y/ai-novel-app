/**
 * 前端组件 - 单元测试
 * 运行方式: 在浏览器控制台执行或用测试框架
 */

// 测试工具函数
const assert = (condition, message) => {
  if (!condition) throw new Error(`Assertion failed: ${message}`);
};

const test = (name, fn) => {
  try {
    fn();
    console.log(`✓ ${name}`);
  } catch (e) {
    console.error(`✗ ${name}`);
    console.error(e.message);
  }
};

// ============ TensionMeter 测试 ============

test('TensionMeter.update() 更新数据', () => {
  const data = { conflict: 0.8, suspense: 0.6, emotion: 0.7, rhythm: 0.5, overall: 0.65 };
  
  // 模拟组件
  const meter = { data: {}, render: () => {} };
  meter.update = TensionMeter.prototype.update;
  meter.update.call(meter, data);
  
  assert(meter.data.conflict === 0.8, 'conflict should be 0.8');
  assert(meter.data.overall === 0.65, 'overall should be 0.65');
});

test('TensionMeter.render() 生成正确HTML结构', () => {
  const container = { innerHTML: '' };
  const meter = { 
    container, 
    data: { conflict: 0.5, suspense: 0.5, emotion: 0.5, rhythm: 0.5, overall: 0.5 },
    render: TensionMeter.prototype.render
  };
  meter.render.call(meter);
  
  assert(container.innerHTML.includes('张力仪表盘'), 'should contain title');
  assert(container.innerHTML.includes('冲突'), 'should contain conflict label');
  assert(container.innerHTML.includes('悬念'), 'should contain suspense label');
  assert(container.innerHTML.includes('tension-fill'), 'should contain tension bar');
});

// ============ ChapterList 测试 ============

test('ChapterList.update() 更新章节列表', () => {
  const list = { chapters: [], render: () => {} };
  list.update = ChapterList.prototype.update;
  
  const chapters = [
    { id: '1', number: 1, title: '第一章', status: 'completed', wordCount: 1000 },
    { id: '2', number: 2, title: '第二章', status: 'writing', wordCount: 500 }
  ];
  
  list.update.call(list, chapters);
  
  assert(list.chapters.length === 2, 'should have 2 chapters');
  assert(list.chapters[0].title === '第一章', 'first chapter title should be correct');
});

test('ChapterList.getStatusColor() 返回正确颜色', () => {
  const list = { getStatusColor: ChapterList.prototype.getStatusColor };
  
  assert(list.getStatusColor('draft') === '#a0a0a0', 'draft should be gray');
  assert(list.getStatusColor('writing') === '#fbbf24', 'writing should be yellow');
  assert(list.getStatusColor('completed') === '#4ade80', 'completed should be green');
});

// ============ RelationGraph 测试 ============

test('RelationGraph.update() 更新角色关系', () => {
  const graph = { characters: [], relations: [], render: () => {} };
  graph.update = RelationGraph.prototype.update;
  
  const characters = [
    { id: 'c1', name: '李昂' },
    { id: 'c2', name: '苏晴' }
  ];
  const relations = [
    { id: 'r1', characterA: 'c1', characterB: 'c2', relationType: '朋友' }
  ];
  
  graph.update.call(graph, characters, relations);
  
  assert(graph.characters.length === 2, 'should have 2 characters');
  assert(graph.relations.length === 1, 'should have 1 relation');
});

test('RelationGraph.getCharName() 返回正确角色名', () => {
  const graph = { 
    characters: [{ id: 'c1', name: '李昂' }],
    getCharName: RelationGraph.prototype.getCharName
  };
  
  assert(graph.getCharName('c1') === '李昂', 'should return correct name');
  assert(graph.getCharName('unknown') === '?', 'unknown should return ?');
});

// ============ KnowledgeBase 测试 ============

test('KnowledgeBase.update() 更新伏笔数据', () => {
  const kb = { foreshadows: [], tabs: 'foreshadow', render: () => {} };
  kb.update = KnowledgeBase.prototype.update;
  
  const foreshadows = [
    { id: 'f1', keyword: '神秘令牌', status: 'planted' },
    { id: 'f2', keyword: '身世之谜', status: 'triggered' }
  ];
  
  kb.update.call(kb, foreshadows);
  
  assert(kb.foreshadows.length === 2, 'should have 2 foreshadows');
});

test('KnowledgeBase.renderForeshadows() 正确渲染伏笔列表', () => {
  const kb = {
    foreshadows: [
      { keyword: '神秘令牌', description: '测试', status: 'planted' }
    ],
    tabs: 'foreshadow',
    renderForeshadows: KnowledgeBase.prototype.renderForeshadows
  };
  
  const html = kb.renderForeshadows.call(kb);
  
  assert(html.includes('神秘令牌'), 'should contain keyword');
  assert(html.includes('已埋'), 'should contain status text');
});

console.log('所有前端测试完成');

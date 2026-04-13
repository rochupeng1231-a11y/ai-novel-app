# 前端测试说明

## 运行方式

### 方式1: 浏览器控制台
1. 打开 `frontend/index.html`
2. 打开浏览器开发者工具 (F12)
3. 切换到 Console 标签
4. 复制 `tests/frontend/test_*.js` 内容到控制台执行

### 方式2: 集成测试
在 `app.js` 加载后，在浏览器控制台执行测试脚本

## 测试覆盖

| 组件 | 测试项 |
|-----|--------|
| TensionMeter | 数据更新、HTML生成 |
| ChapterList | 章节列表更新、状态颜色 |
| RelationGraph | 角色关系更新、名称查找 |
| KnowledgeBase | 伏笔数据更新、渲染逻辑 |

## 添加新测试

在 `tests/frontend/test_*.js` 中添加新的测试文件：

```javascript
test('测试名称', () => {
  // 测试逻辑
  assert(condition, '失败消息');
});
```

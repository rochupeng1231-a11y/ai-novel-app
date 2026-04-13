"""
写作 API - 功能测试
"""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.main import app


client = TestClient(app)


class TestWritingAPI:
    """写作API功能测试"""
    
    def test_write_continue(self):
        """测试续写功能"""
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "续写",
            "context": "上文内容"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'content' in data
        assert 'tension_score' in data
        assert 'tokens_used' in data
    
    def test_write_polish(self):
        """测试润色功能"""
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "润色",
            "context": "要润色的内容"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'content' in data
    
    def test_write_rewrite(self):
        """测试改写功能"""
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "改写"
        })
        
        assert response.status_code == 200
    
    def test_write_summarize(self):
        """测试概括功能"""
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "概括"
        })
        
        assert response.status_code == 200
    
    def test_write_without_context(self):
        """测试不带上下文的写作"""
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "续写"
        })
        
        assert response.status_code == 200
    
    def test_stop_task(self):
        """测试停止写作任务"""
        # 先启动一个任务
        response = client.post("/api/writing", json={
            "chapter_id": "test-chapter",
            "instruction": "续写"
        })
        
        # 停止任务
        response = client.post("/api/writing/stop/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['task_id'] == 'test-task-id'
    
    def test_get_status(self):
        """测试获取任务状态"""
        response = client.get("/api/writing/status/nonexistent")
        
        # 不存在的任务返回404
        assert response.status_code == 404

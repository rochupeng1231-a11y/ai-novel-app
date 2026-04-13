"""
章节 API - 功能测试
"""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.main import app


client = TestClient(app)


class TestChaptersAPI:
    """章节API功能测试"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert 'version' in response.json()
    
    def test_health(self):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
    
    def test_create_chapter(self):
        """测试创建章节"""
        response = client.post("/api/chapters/", json={
            "project_id": "test-project",
            "number": 1,
            "title": "第一章"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['number'] == 1
        assert data['title'] == "第一章"
    
    def test_get_chapters_empty(self):
        """测试获取空项目章节"""
        response = client.get("/api/chapters/project/test-project")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_chapter_not_found(self):
        """测试获取不存在的章节"""
        response = client.get("/api/chapters/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_update_chapter_not_found(self):
        """测试更新不存在的章节"""
        response = client.put("/api/chapters/nonexistent-id", json={
            "title": "新标题"
        })
        
        assert response.status_code == 404
    
    def test_delete_chapter(self):
        """测试删除章节"""
        response = client.delete("/api/chapters/test-id")
        
        assert response.status_code == 200
        assert response.json()['message'] == 'Deleted'

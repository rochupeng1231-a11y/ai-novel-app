"""
角色 API - 功能测试
"""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.main import app


client = TestClient(app)


class TestCharactersAPI:
    """角色API功能测试"""
    
    def test_create_character(self):
        """测试创建角色"""
        response = client.post("/api/characters/", json={
            "project_id": "test-project",
            "name": "李昂",
            "alias": "昂哥",
            "personality": "冷静、理智",
            "speech_style": "简洁有力",
            "forbidden_topics": ["过去", "家庭"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "李昂"
        assert data['alias'] == "昂哥"
        assert data['forbidden_topics'] == ["过去", "家庭"]
    
    def test_get_characters_empty(self):
        """测试获取空项目角色"""
        response = client.get("/api/characters/project/test-project")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_character_not_found(self):
        """测试获取不存在的角色"""
        response = client.get("/api/characters/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_update_character_not_found(self):
        """测试更新不存在的角色"""
        response = client.put("/api/characters/nonexistent-id", json={
            "name": "新名字"
        })
        
        assert response.status_code == 404
    
    def test_delete_character(self):
        """测试删除角色"""
        response = client.delete("/api/characters/test-id")
        
        assert response.status_code == 200
        assert response.json()['message'] == 'Deleted'

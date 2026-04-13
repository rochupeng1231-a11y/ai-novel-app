"""
版本控制服务 - 单元测试
"""
import pytest
import sys
sys.path.insert(0, '/root/.openclaw/agents/team-leader/workspace/ai-novel-app')

from backend.services.version_control import VersionControl


class TestVersionControl:
    """版本控制测试"""
    
    def setup_method(self):
        """每个测试方法前执行"""
        self.vc = VersionControl()
    
    def test_save_first_version(self):
        """测试保存第一个版本"""
        chapter_id = "ch-1"
        content = "第一章内容"
        
        version_num = self.vc.save_version(chapter_id, content)
        
        assert version_num == 1
    
    def test_save_multiple_versions(self):
        """测试保存多个版本"""
        chapter_id = "ch-1"
        
        v1 = self.vc.save_version(chapter_id, "版本1")
        v2 = self.vc.save_version(chapter_id, "版本2")
        v3 = self.vc.save_version(chapter_id, "版本3")
        
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3
    
    def test_get_version(self):
        """测试获取指定版本"""
        chapter_id = "ch-1"
        self.vc.save_version(chapter_id, "版本1")
        self.vc.save_version(chapter_id, "版本2")
        
        version = self.vc.get_version(chapter_id, 1)
        
        assert version is not None
        assert version['content'] == "版本1"
        assert version['version_number'] == 1
    
    def test_get_nonexistent_version(self):
        """测试获取不存在的版本"""
        version = self.vc.get_version("ch-1", 999)
        
        assert version is None
    
    def test_list_versions(self):
        """测试列出所有版本"""
        chapter_id = "ch-1"
        self.vc.save_version(chapter_id, "版本1")
        self.vc.save_version(chapter_id, "版本2")
        
        versions = self.vc.list_versions(chapter_id)
        
        assert len(versions) == 2
        assert versions[0]['version_number'] == 1
        assert versions[1]['version_number'] == 2
    
    def test_list_versions_empty(self):
        """测试列出不存在章节的版本"""
        versions = self.vc.list_versions("ch-nonexistent")
        
        assert versions == []
    
    def test_rollback(self):
        """测试回滚功能"""
        chapter_id = "ch-1"
        self.vc.save_version(chapter_id, "版本1")
        self.vc.save_version(chapter_id, "版本2")
        
        success = self.vc.rollback(chapter_id, 1)
        
        assert success is True
    
    def test_rollback_nonexistent(self):
        """测试回滚不存在的版本"""
        success = self.vc.rollback("ch-1", 999)
        
        assert success is False
    
    def test_independent_chapters(self):
        """测试不同章节版本独立"""
        self.vc.save_version("ch-1", "ch1-v1")
        self.vc.save_version("ch-2", "ch2-v1")
        self.vc.save_version("ch-1", "ch1-v2")
        
        versions_ch1 = self.vc.list_versions("ch-1")
        versions_ch2 = self.vc.list_versions("ch-2")
        
        assert len(versions_ch1) == 2
        assert len(versions_ch2) == 1
        assert self.vc.get_version("ch-1", 1)['content'] == "ch1-v1"
        assert self.vc.get_version("ch-2", 1)['content'] == "ch2-v1"

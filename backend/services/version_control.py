"""
版本控制服务
"""
from datetime import datetime
from typing import List, Optional


class VersionControl:
    """章节版本管理"""
    
    def __init__(self):
        # chapter_id -> List[Version]
        self.versions = {}
    
    def save_version(self, chapter_id: str, content: str) -> int:
        """保存版本，返回版本号"""
        if chapter_id not in self.versions:
            self.versions[chapter_id] = []
        
        version_number = len(self.versions[chapter_id]) + 1
        self.versions[chapter_id].append({
            "version_number": version_number,
            "content": content,
            "created_at": datetime.now()
        })
        return version_number
    
    def get_version(self, chapter_id: str, version_number: int) -> Optional[dict]:
        """获取指定版本"""
        if chapter_id not in self.versions:
            return None
        
        for v in self.versions[chapter_id]:
            if v["version_number"] == version_number:
                return v
        return None
    
    def list_versions(self, chapter_id: str) -> List[dict]:
        """列出所有版本"""
        if chapter_id not in self.versions:
            return []
        return [
            {"version_number": v["version_number"], "created_at": v["created_at"]}
            for v in self.versions[chapter_id]
        ]
    
    def rollback(self, chapter_id: str, version_number: int) -> bool:
        """回滚到指定版本"""
        version = self.get_version(chapter_id, version_number)
        if version:
            # TODO: 更新章节内容
            return True
        return False

"""
测试运行脚本 - 后端单元测试
"""
import subprocess
import sys


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("运行 AI 写小说应用 - 测试套件")
    print("=" * 50)
    
    # 运行 pytest
    result = subprocess.run(
        ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        cwd='/root/.openclaw/agents/team-leader/workspace/ai-novel-app',
        capture_output=False
    )
    
    return result.returncode


if __name__ == '__main__':
    sys.exit(run_tests())

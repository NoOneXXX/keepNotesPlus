"""
Git 管理器 - 处理 Git 操作（pull、push、commit、merge、冲突解决）
"""
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, List


class GitManager:
    """Git 操作管理类"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.config_file = os.path.join(repo_path, ".git_config.json")
        self._load_config()
    
    def _load_config(self):
        """加载 Git 配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}
    
    def _save_config(self):
        """保存 Git 配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def is_git_repo(self) -> bool:
        """检查是否是 Git 仓库"""
        git_dir = os.path.join(self.repo_path, ".git")
        return os.path.exists(git_dir)
    
    def init_repo(self) -> Tuple[bool, str]:
        """初始化 Git 仓库"""
        try:
            result = subprocess.run(
                ["git", "init"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, "Git 仓库初始化成功"
            return False, f"初始化失败: {result.stderr}"
        except Exception as e:
            return False, f"初始化异常: {str(e)}"
    
    def set_remote(self, remote_name: str, remote_url: str) -> Tuple[bool, str]:
        """设置远程仓库"""
        try:
            # 先检查是否已存在
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                # 远程已存在，更新
                result = subprocess.run(
                    ["git", "remote", "set-url", remote_name, remote_url],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
            else:
                # 添加新的远程
                result = subprocess.run(
                    ["git", "remote", "add", remote_name, remote_url],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
            
            if result.returncode == 0:
                self.config['remote'] = remote_url
                self._save_config()
                return True, f"远程仓库设置成功: {remote_url}"
            return False, f"设置失败: {result.stderr}"
        except Exception as e:
            return False, f"设置异常: {str(e)}"
    
    def get_remote_url(self) -> Optional[str]:
        """获取远程仓库 URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def get_status(self) -> Tuple[bool, dict]:
        """获取仓库状态"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            status = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': [],
                'conflicted': []
            }
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    code = line[:2]
                    file_path = line[3:]
                    
                    if 'M' in code:
                        status['modified'].append(file_path)
                    elif 'A' in code:
                        status['added'].append(file_path)
                    elif 'D' in code:
                        status['deleted'].append(file_path)
                    elif 'U' in code:
                        status['conflicted'].append(file_path)
                    elif '??' in code:
                        status['untracked'].append(file_path)
                
                return True, status
            return False, status
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_current_branch(self) -> Optional[str]:
        """获取当前分支名"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def get_branches(self) -> List[str]:
        """获取所有分支"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                branches = []
                for line in result.stdout.strip().split('\n'):
                    branch = line.strip().replace('* ', '').replace('remotes/origin/', '')
                    if branch and not branch.startswith('HEAD'):
                        branches.append(branch)
                return list(set(branches))
            return []
        except:
            return []
    
    def add_all(self) -> Tuple[bool, str]:
        """添加所有更改到暂存区"""
        try:
            result = subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, "已添加所有更改到暂存区"
            return False, f"添加失败: {result.stderr}"
        except Exception as e:
            return False, f"添加异常: {str(e)}"
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """提交更改"""
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, f"提交成功: {message}"
            return False, f"提交失败: {result.stderr}"
        except Exception as e:
            return False, f"提交异常: {str(e)}"
    
    def pull(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """拉取远程更改"""
        try:
            if branch is None:
                branch = self.get_current_branch() or "main"
            
            result = subprocess.run(
                ["git", "pull", remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, f"拉取成功: {remote}/{branch}"
            return False, f"拉取失败: {result.stderr}"
        except Exception as e:
            return False, f"拉取异常: {str(e)}"
    
    def push(self, remote: str = "origin", branch: str = None) -> Tuple[bool, str]:
        """推送到远程"""
        try:
            if branch is None:
                branch = self.get_current_branch() or "main"
            
            result = subprocess.run(
                ["git", "push", remote, branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, f"推送成功: {remote}/{branch}"
            return False, f"推送失败: {result.stderr}"
        except Exception as e:
            return False, f"推送异常: {str(e)}"
    
    def merge(self, branch: str) -> Tuple[bool, str]:
        """合并分支"""
        try:
            result = subprocess.run(
                ["git", "merge", branch],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return True, f"合并成功: {branch}"
            return False, f"合并失败: {result.stderr}"
        except Exception as e:
            return False, f"合并异常: {str(e)}"
    
    def has_conflicts(self) -> bool:
        """检查是否有冲突"""
        success, status = self.get_status()
        if success:
            return len(status.get('conflicted', [])) > 0
        return False
    
    def resolve_conflicts_auto(self) -> Tuple[bool, str]:
        """自动解决冲突（保留本地版本）"""
        try:
            success, status = self.get_status()
            if not success:
                return False, "无法获取状态"
            
            conflicted = status.get('conflicted', [])
            if not conflicted:
                return True, "没有冲突需要解决"
            
            resolved = []
            for file_path in conflicted:
                full_path = os.path.join(self.repo_path, file_path)
                # 使用 --ours 策略保留本地版本
                result = subprocess.run(
                    ["git", "checkout", "--ours", file_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if result.returncode == 0:
                    # 添加到暂存区
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.repo_path,
                        capture_output=True
                    )
                    resolved.append(file_path)
            
            return True, f"已自动解决 {len(resolved)} 个冲突文件"
        except Exception as e:
            return False, f"解决冲突异常: {str(e)}"
    
    def resolve_conflicts_theirs(self) -> Tuple[bool, str]:
        """自动解决冲突（保留远程版本）"""
        try:
            success, status = self.get_status()
            if not success:
                return False, "无法获取状态"
            
            conflicted = status.get('conflicted', [])
            if not conflicted:
                return True, "没有冲突需要解决"
            
            resolved = []
            for file_path in conflicted:
                # 使用 --theirs 策略保留远程版本
                result = subprocess.run(
                    ["git", "checkout", "--theirs", file_path],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                if result.returncode == 0:
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.repo_path,
                        capture_output=True
                    )
                    resolved.append(file_path)
            
            return True, f"已自动解决 {len(resolved)} 个冲突文件（使用远程版本）"
        except Exception as e:
            return False, f"解决冲突异常: {str(e)}"
    
    def get_commit_log(self, count: int = 10) -> List[dict]:
        """获取提交日志"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%an|%ad|%s", "--date=short"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logs = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        logs.append({
                            'hash': parts[0],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
                return logs
            return []
        except:
            return []
    
    def sync_all(self, commit_message: str = "Auto sync") -> Tuple[bool, str]:
        """完整同步流程：添加、提交、拉取、推送"""
        try:
            # 1. 添加所有更改
            success, msg = self.add_all()
            if not success:
                return False, f"添加失败: {msg}"
            
            # 2. 提交
            success, msg = self.commit(commit_message)
            if not success and "nothing to commit" not in msg:
                return False, f"提交失败: {msg}"
            
            # 3. 拉取远程更改
            success, msg = self.pull()
            if not success:
                # 检查是否有冲突
                if self.has_conflicts():
                    # 自动解决冲突
                    success, msg = self.resolve_conflicts_auto()
                    if not success:
                        return False, f"冲突解决失败: {msg}"
                    # 重新提交
                    self.commit(f"{commit_message} - 冲突已解决")
            
            # 4. 推送
            success, msg = self.push()
            if not success:
                return False, f"推送失败: {msg}"
            
            return True, "同步成功"
        except Exception as e:
            return False, f"同步异常: {str(e)}"

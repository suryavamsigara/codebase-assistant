from pathlib import Path
from tree_sitter import Language, Parser, Tree, Node
import tree_sitter_python as tspython
from typing import Generator

class RepoWalker:
    def __init__(self, repo_path: str, repo_name: str): # repo_path: tmp/r1
        self.cwd: Path = Path.cwd()
        self.repo_path: Path = (self.cwd / repo_path).resolve()
        self.repo_name = Path(repo_name)

        self.skip_dirs = {"venv", ".venv", ".env", "node_modules", "dist", ".git", "__pycache__"}

        self.skip_files = {".env", "uv.lock"}

    def get_git_info(self):
        return ""
    
    def walk(self):
        """Yields file paths and meta data"""
        cwd: Path = Path.cwd()
        target_dir: Path = (cwd / self.repo_path).resolve()

        if not target_dir.is_relative_to(cwd):
            print(f"Directory {target_dir} is outside current working directory")
            # return
        
        if not target_dir.is_dir():
            print(f"Directory {target_dir} doesn't exist")
            # return
        
        if not target_dir.is_dir():
            print(f"{target_dir} is not a directory.")
            # return

        for root, dirs, files in target_dir.walk(): # (Path, List[str], List[str])
            # print(f"Root: {root}, dirs: {dirs}, files: {files}")

            for file in files:
                file_path = (Path(root) / file).resolve()

                yield {
                    'file_path': str(file_path.relative_to(self.repo_path)),
                    'absolute_path': file_path,
                    'repo_name': self.repo_name,
                    'language': 'Python',
                } # language, git author, last modified
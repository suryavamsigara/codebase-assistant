from pathlib import Path

class RepoWalker:
    def __init__(self, repo_path: str, repo_name: str): # repo_path: tmp/r1
        self.cwd: Path = Path.cwd()
        self.repo_path: Path = (self.cwd / repo_path).resolve()
        self.repo_name = Path(repo_name)

        self.skip_dirs = {
            "venv", ".venv", ".env", "node_modules", "dist", ".git",
            "__pycache__", "build", ".next", ".cache", ".pytest_cache",
            ".vscode", "public"
        }

        self.skip_files = {
            ".env", "uv.lock", "yarn.lock", "package-lock.json", "README.md", ".gitignore", 
        }

        self.extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.md': 'markdown',
            '.toml': 'toml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }

    def get_git_info(self):
        return ""
    
    def walk(self):
        """Yields file paths and meta data"""
        target_dir: Path = self.repo_path
        
        if not target_dir.is_dir():
            print(f"Directory {target_dir} doesn't exist")
            return

        for root, dirs, files in target_dir.walk(): # (Path, List[str], List[str])
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                if file in self.skip_files:
                    continue

                file_path = root / file
                ext = file_path.suffix.lower()

                if ext not in self.extensions:
                    language = 'markdown'
                else:
                    language = self.extensions[ext]
                
                print(f"Yielding file : {file_path}")

                yield {
                    'file_path': str(file_path.relative_to(self.repo_path)),
                    'absolute_path': file_path,
                    'repo_name': self.repo_name,
                    'language': language,
                } # git author, last modified
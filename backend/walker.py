from pathlib import Path

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
        target_dir: Path = self.repo_path
        
        if not target_dir.is_dir():
            print(f"Directory {target_dir} doesn't exist")
            return

        for root, dirs, files in target_dir.walk(): # (Path, List[str], List[str])
            # print(f"Root: {root}, dirs: {dirs}, files: {files}")

            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for file in files:
                if file in self.skip_files:
                    continue

                file_path = root / file
                if not file_path.suffix == ".py":
                    continue
                
                print(f"Yielding file : {file_path}")

                yield {
                    'file_path': str(file_path.relative_to(self.repo_path)),
                    'absolute_path': file_path,
                    'repo_name': self.repo_name,
                    'language': 'Python',
                } # language, git author, last modified
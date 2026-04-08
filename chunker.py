import os
from pathlib import Path
from tree_sitter import Language, Parser, Tree, Node
import tree_sitter_python as tspython
from typing import Generator, List

EXCLUDE_DIRS = {"venv", ".venv", "env", "node_modules", ".git", "__pycache__"}

def walk(directory: str = "."):
    cwd: Path = Path.cwd()
    target_dir: Path = (cwd / directory).resolve()

    if not target_dir.is_relative_to(cwd):
        print(f"Directory {directory} is outside current working directory.")
        return
    
    if not target_dir.exists():
        print(f"Directory {directory} doesn't exist")

    if not target_dir.is_dir():
        print(f"{directory} is not a directory")

    for root, dirs, files in target_dir.walk(): # (Path, List[str], List[str])
        print(f"Root: {root}, dirs: {dirs}, files: {files}")
        
        for file in files:
            # get file path
            # skip files

            # yield file_path (relative to repo, absolute), language, repo_name, git_author, last_modified
            # run - for file_data in walk(): print(processing: file_data[file_path])

            file_path = Path(root) / file

            yield {
                'file_path': str(file_path.is_relative_to(directory)),
                'absolute_path': file_path,
            }
    

PY_LANGUAGE = Language(tspython.language())


def traverse_tree(tree: Tree) -> Generator[Node, None, None]:
    cursor = tree.walk()

    visited_children = False

    while True:
        if not visited_children:
            yield cursor.node

            if not cursor.goto_first_child():
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent():
            break

def chunk_python(code: str) -> List:
    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf-8'))
    root = tree.root_node

    chunks = []

    for node in traverse_tree(tree):
        if node.type == "function_definition":
            name_node = node.child_by_field_name('name')

            if name_node:
                name = code[name_node.start_byte:name_node.end_byte]

                body_node = node.child_by_field_name('body')
                body = code[body_node.start_byte:body_node.end_byte] if body_node else ""

                chunks.append({
                    'type': 'function',
                    'name': name,
                    'code': code,
                    'body': body,
                    'start_line': node.start_point[0] + 1,
                    'end_line': node.end_point[0] + 1
                })
    return chunks


def main():
    for file_data in walk("tmp/r1"):
        print(f"Processing: {file_data['file_path']}")

        with open(file_data['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        chunks = chunk_python(code)

        for chunk in chunks:
            print(f"\nName: {chunk['name']}\nBody: {chunk['body']}\n===================================\n")

if __name__ == "__main__":
    main()
